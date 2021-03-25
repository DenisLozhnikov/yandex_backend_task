from rest_framework import generics, status
from rest_framework.response import Response
from candy.serializers import *
from candy.models import *
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from statistics import mean


def parse_list(self, request, verbose, name, times_name):
    """
    выполнят парсинг переданного списка
    :param request: запрос для парсинга
    :param verbose: Вывод при невалидном запросе
    :param name: имя выводимиого поля
    :param times_name: названия поля с временем работы/доставки
    :return: 201 CREATED или 400 BAD REQUEST со списком id
    """
    req_data = request.data.copy()
    parse_data = req_data.pop('data')
    serializers_data = []
    validation_error = []
    for item in parse_data:
        serializer = self.get_serializer(data=item)
        if serializer.is_valid():
            try:
                parse_time(serializer.data[times_name])
                serializers_data.append({"id": serializer.data[name]})
            except ValueError:
                validation_error.append({"id": serializer.data[name]})
        else:
            validation_error.append({"id": serializer.data[name]})

    if not validation_error:
        for item in parse_data:
            serializer = self.get_serializer(data=item)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        return Response({verbose: serializers_data}, status=status.HTTP_201_CREATED)
    else:
        return Response({"validation_error": {verbose: validation_error}}, status=status.HTTP_400_BAD_REQUEST)


def parse_time(strs):
    """
    парсит передаваемое время с помощью библиотеки datetime
    :param strs: список строк формата HH:MM-HH:MM
    :return: список объектов формата {"start": datetime.time,
                                      "end": datetime.time}
    """
    times = []
    for item in strs:
        stamps = item.split("-")
        start = datetime.strptime(stamps[0], "%H:%M").time()
        end = datetime.strptime(stamps[1], "%H:%M").time()
        obj = {"start": start, "end": end}
        times.append(obj)
    return times


def time_matches(work_times, del_times):
    """
    проверяет, перескаются ли переданные промежутки времени
    :param work_times, :param del_times список объектов формата {"start": datetime.time,
                                                                 "end": datetime.time}
    :return: bool
    """
    for wtime in work_times:
        for dtime in del_times:
            if wtime["start"] < dtime["end"] and wtime["end"] > dtime["start"]:
                return True
    return False


class CreateCourier(generics.CreateAPIView):
    """
    POST /couriers
    импорт курьеров
    """
    serializer_class = CourierDetail
    queryset = Courier.objects.all()

    def create(self, request, *args, **kwargs):
        return parse_list(self, request, "couriers", "courier_id", "working_hours")


def check_mod(self, req_data):
    try:
        if req_data.pop('courier_id') != self.get_serializer(self.get_object()).data['courier_id']:
            return False
        return True
    except KeyError:
        return True


class PatchCourier(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourierDetail
    queryset = Courier.objects.all()

    def get(self, request, *args, **kwargs):
        """
        GET /couriers/<courier_id>
        Вывод информации о курьере
        """
        try:
            completed_orders = CompletedOrders.objects.filter(courier_id=self.kwargs.get('pk'))
            if not completed_orders:
                raise ObjectDoesNotExist
            orders_by_regions = {}
            total_earnings = 0
            for order in completed_orders:
                order_info = Order.objects.get(order_id=order.order_id)
                order_type = order_info.assigned_type
                if order_type == 'foot':
                    c = 2
                elif order_type == 'bike':
                    c = 5
                else:
                    c = 9
                total_earnings += 500 * c
                if order_info.region in orders_by_regions:
                    orders_by_regions[order_info.region].append(order.complete_time)
                else:
                    orders_by_regions[order_info.region] = [order.complete_time]
            td = []
            tdr = []
            for region, times in orders_by_regions.items():
                initial_time = ActiveCouriers.objects.get(active_id=self.kwargs.get('pk')).assigned_time
                sorted_orders = sorted(times)
                tdr.append((sorted_orders[0] - initial_time).total_seconds())
                for i in range(len(sorted_orders) - 1):
                    tdr.append((sorted_orders[i + 1] - sorted_orders[i]).total_seconds())
                td.append(mean(tdr))

            t = -min(td)
            rating = round((60 * 60 - min(t, 60 * 60)) / (60 * 60) * 5, 2)

            cour = Courier.objects.get(courier_id=self.kwargs.get('pk'))
            cour.rating = rating
            cour.earnings = total_earnings
            cour.save()

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return self.retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        completed_orders = CompletedOrders.objects.filter(courier_id=self.kwargs.get('pk'))
        if not completed_orders:
            return self.serializer_class
        return CourierReport

    def patch(self, request, *args, **kwargs):
        """
        PATCH /couriers/<courier_id>
        обновление информации о курьере
        """
        req_data = request.data.copy()
        if not check_mod(self, req_data):
            return Response({"courier_id": "Not allowed to modify"}, status=status.HTTP_400_BAD_REQUEST)
        to_response = self.partial_update(request, *args, **kwargs)
        courier = Courier.objects.get(courier_id=self.kwargs.get('pk'))
        try:
            print("access")
            assigned_orders = ActiveCouriers.objects.get(active_id=self.kwargs.get('pk'))
            if "courier_type" in req_data:
                c_type = req_data.pop('courier_type')
            else:
                c_type = courier.courier_type
            if c_type == 'foot':
                capacity = 10
            elif c_type == 'bike':
                capacity = 15
            else:
                capacity = 50

            if "working_hours" in req_data:
                try:
                    courier_active_hours = parse_time(req_data.pop('working_hours'))
                except ValueError:
                    return Response({"working_hours": "bad time format"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                courier_active_hours = parse_time(courier.working_hours)

            if "regions" in req_data:
                active_regions = req_data.pop('regions')
            else:
                active_regions = courier.regions
            weight = 0
            update_orders = []
            for active_order_id in assigned_orders.orders:
                order = Order.objects.get(order_id=active_order_id)
                order_time = parse_time(order.delivery_hours)
                if time_matches(courier_active_hours, order_time) and (
                        weight + order.weight) <= capacity and order.region in active_regions:
                    weight += order.weight
                    update_orders.append(order.order_id)
                else:
                    order.is_available = True
                    order.save()
            assigned_orders.orders = update_orders
            assigned_orders.save()
        except ObjectDoesNotExist:
            pass

        return to_response


class CreateOrders(generics.CreateAPIView):
    """
    POST /orders
    импорт заказов
    """
    serializer_class = OrderDetail
    queryset = Order.objects.all()

    def create(self, request, *args, **kwargs):
        return parse_list(self, request, "orders", "order_id", "delivery_hours")


class Assign(generics.CreateAPIView):
    """
    POST /orders/assign
    назначение заказа для переданного courier_id
    """
    serializer_class = GetCourierId

    def post(self, request, *args, **kwargs):
        try:
            req_data = request.data.copy().pop('courier_id')
        except ObjectDoesNotExist:
            return Response({"validation_error": "courier_id"}, status=status.HTTP_400_BAD_REQUEST)
        free_orders = Order.objects.filter(is_available=True)
        try:
            courier = Courier.objects.get(courier_id=req_data)
        except ObjectDoesNotExist:
            return Response({"DoesNotExist": {"courier_id": req_data}}, status=status.HTTP_400_BAD_REQUEST)

        weight = 0
        response_orders = []
        try:
            assigned_orders = ActiveCouriers.objects.get(active_id=req_data)
            if not assigned_orders.orders:
                assigned_time = assigned_orders.assigned_time
            else:
                assigned_time = datetime.now(timezone.utc).isoformat()
            assigned_orders = assigned_orders.orders
            for order in assigned_orders:
                order_weight = Order.objects.get(order_id=order).weight
                response_orders.append({"id": order})
                weight += order_weight
        except ObjectDoesNotExist:
            assigned_orders = []
            assigned_time = datetime.now(timezone.utc).isoformat()
        c_type = courier.courier_type
        if c_type == 'foot':
            capacity = 10
        elif c_type == 'bike':
            capacity = 15
        else:
            capacity = 50
        courier_active_hours = parse_time(courier.working_hours)
        for order in free_orders:
            order_time = parse_time(order.delivery_hours)
            order_region = order.region
            if time_matches(courier_active_hours, order_time) and (
                    weight + order.weight) <= capacity and order_region in courier.regions:
                assigned_orders.append(order.order_id)
                response_orders.append({"id": order.order_id})
                order.is_available = False
                order.assigned_type = c_type
                order.save()
                weight += order.weight
        records = ActiveCouriers(active_id=req_data, orders=assigned_orders, assigned_time=assigned_time)
        records.save()
        if not response_orders:
            return Response({"orders": []}, status=status.HTTP_200_OK)
        return Response(
            {"orders": response_orders, "assigned_time": records.assigned_time},
            status=status.HTTP_200_OK)


class CompleteOrder(generics.CreateAPIView):
    """
    POST /orders/complete
    Отмечает заказ как выполненный
    """
    serializer_class = OrderFinished

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_data = request.data.copy()
        try:
            active_orders = ActiveCouriers.objects.get(active_id=req_data.pop('courier_id'))
            order_id = req_data.pop('order_id')
            if order_id in active_orders.orders:
                active_orders.orders.remove(order_id)
                active_orders.save()
            else:
                raise ObjectDoesNotExist
        except ObjectDoesNotExist:
            return Response({"validation_error": serializer.data}, status=status.HTTP_400_BAD_REQUEST)

        return self.create(request, *args, **kwargs)
