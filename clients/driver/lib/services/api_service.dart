import 'package:dio/dio.dart';
import '../models/route_model.dart';
import 'storage_service.dart';

class PackageModel {
  final String id;
  final String packageId;
  final String status;
  final String? priority;
  final double? lat;
  final double? lon;
  final String? addressSummary;
  final DateTime? createdAt;

  PackageModel({
    required this.id,
    required this.packageId,
    required this.status,
    this.priority,
    this.lat,
    this.lon,
    this.addressSummary,
    this.createdAt,
  });

  factory PackageModel.fromJson(Map<String, dynamic> json) {
    return PackageModel(
      id: json['id'] ?? '',
      packageId: json['package_id'] ?? '',
      status: json['status'] ?? 'pending',
      priority: json['priority'],
      lat: json['lat']?.toDouble(),
      lon: json['lon']?.toDouble(),
      addressSummary: json['address_summary'],
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'])
          : null,
    );
  }
}

class ApiService {
  late Dio _dio;
  final StorageService _storage = StorageService();
  
  ApiService() {
    _dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));
  }
  
  Future<String> get _baseUrl async {
    return await _storage.getServerUrl();
  }
  
  // ============ Packages API ============
  
  Future<List<PackageModel>> getPackages({String? status}) async {
    try {
      final baseUrl = await _baseUrl;
      final queryParams = <String, dynamic>{};
      if (status != null) {
        queryParams['status'] = status;
      }
      
      final response = await _dio.get(
        '$baseUrl/api/v1/packages/',
        queryParameters: queryParams,
      );
      
      if (response.statusCode == 200) {
        final packages = (response.data['packages'] as List?)
            ?.map((e) => PackageModel.fromJson(e))
            .toList() ?? [];
        return packages;
      }
      return [];
    } catch (e) {
      print('Error fetching packages: $e');
      return [];
    }
  }
  
  Future<List<PackageModel>> getPackagesReadyForDelivery() async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.get('$baseUrl/api/v1/packages/ready-for-delivery');
      
      if (response.statusCode == 200) {
        final packages = (response.data['packages'] as List?)
            ?.map((e) => PackageModel.fromJson(e))
            .toList() ?? [];
        return packages;
      }
      return [];
    } catch (e) {
      print('Error fetching packages ready for delivery: $e');
      return [];
    }
  }
  
  Future<Map<String, dynamic>?> getPackageStats() async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.get('$baseUrl/api/v1/packages/stats');
      
      if (response.statusCode == 200) {
        return response.data;
      }
      return null;
    } catch (e) {
      print('Error fetching package stats: $e');
      return null;
    }
  }
  
  Future<bool> updatePackageStatus(String packageId, String status) async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.patch(
        '$baseUrl/api/v1/packages/$packageId/status',
        queryParameters: {'status': status},
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error updating package status: $e');
      return false;
    }
  }
  
  // ============ Routes API ============
  
  Future<List<RouteModel>> getRoutes() async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.get('$baseUrl/api/v1/routes/');
      
      if (response.statusCode == 200) {
        final routes = (response.data['routes'] as List?)
            ?.map((e) => RouteModel.fromJson(e))
            .toList() ?? [];
        return routes;
      }
      return [];
    } catch (e) {
      print('Error fetching routes: $e');
      return [];
    }
  }
  
  Future<RouteModel?> getRoute(String routeId) async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.get('$baseUrl/api/v1/routes/$routeId');
      
      if (response.statusCode == 200) {
        return RouteModel.fromJson(response.data);
      }
      return null;
    } catch (e) {
      print('Error fetching route: $e');
      return null;
    }
  }
  
  Future<bool> updateStopStatus(String routeId, String stopId, String status) async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.patch(
        '$baseUrl/api/v1/routes/$routeId/stops/$stopId',
        data: {'status': status},
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error updating stop status: $e');
      return false;
    }
  }
  
  // ============ Health Check ============
  
  Future<bool> checkHealth() async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.get('$baseUrl/health');
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
