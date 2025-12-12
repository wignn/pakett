import 'package:dio/dio.dart';
import '../models/route_model.dart';

class ApiService {
  late Dio _dio;
  final String _baseUrl = 'http://localhost:8000';
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ));
  }
  
  Future<List<RouteModel>> getRoutes() async {
    try {
      final response = await _dio.get('/api/v1/routes');
      
      if (response.statusCode == 200) {
        final routes = (response.data['routes'] as List?)
            ?.map((e) => RouteModel.fromJson(e))
            .toList() ?? [];
        return routes;
      }
      return [];
    } catch (e) {
      // Return mock data for demo
      return _getMockRoutes();
    }
  }
  
  Future<RouteModel?> getRoute(String routeId) async {
    try {
      final response = await _dio.get('/api/v1/routes/$routeId');
      
      if (response.statusCode == 200) {
        return RouteModel.fromJson(response.data);
      }
      return null;
    } catch (e) {
      return null;
    }
  }
  
  Future<bool> updateStopStatus(String routeId, String stopId, String status) async {
    try {
      final response = await _dio.patch(
        '/api/v1/routes/$routeId/stops/$stopId',
        data: {'status': status},
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
  
  List<RouteModel> _getMockRoutes() {
    return [
      RouteModel(
        id: 'route-1',
        vehicleId: 'V001',
        driverName: 'Driver A',
        plannedDate: DateTime.now(),
        status: 'planned',
        totalDistanceKm: 25.4,
        totalTimeMinutes: 180,
        stops: [
          RouteStop(
            sequence: 0,
            lat: -6.2088,
            lon: 106.8456,
            addressSummary: 'Depot',
            status: 'completed',
          ),
          RouteStop(
            sequence: 1,
            packageId: 'PKT001',
            lat: -6.225,
            lon: 106.795,
            addressSummary: 'Jalan Sudirman 45, Menteng',
            status: 'pending',
          ),
          RouteStop(
            sequence: 2,
            packageId: 'PKT002',
            lat: -6.235,
            lon: 106.780,
            addressSummary: 'Jalan Thamrin 12, Tanah Abang',
            status: 'pending',
          ),
          RouteStop(
            sequence: 3,
            packageId: 'PKT003',
            lat: -6.215,
            lon: 106.820,
            addressSummary: 'Jalan Gatot Subroto 78, Setiabudi',
            status: 'pending',
          ),
          RouteStop(
            sequence: 4,
            packageId: 'PKT004',
            lat: -6.245,
            lon: 106.810,
            addressSummary: 'Jalan Rasuna Said 33, Kuningan',
            status: 'pending',
          ),
        ],
      ),
    ];
  }
}
