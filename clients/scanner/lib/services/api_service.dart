import 'dart:convert';
import 'package:dio/dio.dart';
import '../models/package_model.dart';
import 'storage_service.dart';

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
  
  Future<PackageModel?> ingestPackage(PackageModel package) async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.post(
        '$baseUrl/api/v1/ingest/ocr-text',
        data: package.toIngestRequest(),
      );
      
      if (response.statusCode == 200) {
        return PackageModel.fromJson(response.data);
      }
      return null;
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout) {
        // Offline - will sync later
        return null;
      }
      rethrow;
    }
  }
  
  Future<Map<String, dynamic>?> parseAddress(String rawText) async {
    try {
      final baseUrl = await _baseUrl;
      final response = await _dio.post(
        '$baseUrl/api/v1/address/parse',
        data: {
          'raw_text': rawText,
          'apply_corrections': true,
        },
      );
      
      if (response.statusCode == 200 && response.data['success'] == true) {
        return response.data['address'];
      }
      return null;
    } catch (e) {
      return null;
    }
  }
  
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
