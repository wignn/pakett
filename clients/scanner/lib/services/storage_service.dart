import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import '../models/package_model.dart';

class StorageService {
  static const String _keyServerUrl = 'server_url';
  static const String _keyDeviceId = 'device_id';
  static const String _keyAutoSync = 'auto_sync';
  static const String _keyConfidenceThreshold = 'confidence_threshold';
  static const String _keyPackages = 'packages';
  static const String _keyPendingSync = 'pending_sync';
  
  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();
  
  // Server URL
  Future<String> getServerUrl() async {
    final prefs = await _prefs;
    return prefs.getString(_keyServerUrl) ?? 'http://localhost:8000';
  }
  
  Future<void> setServerUrl(String url) async {
    final prefs = await _prefs;
    await prefs.setString(_keyServerUrl, url);
  }
  
  // Device ID
  Future<String> getDeviceId() async {
    final prefs = await _prefs;
    var deviceId = prefs.getString(_keyDeviceId);
    if (deviceId == null) {
      deviceId = 'scanner-${const Uuid().v4().substring(0, 8)}';
      await prefs.setString(_keyDeviceId, deviceId);
    }
    return deviceId;
  }
  
  Future<void> setDeviceId(String id) async {
    final prefs = await _prefs;
    await prefs.setString(_keyDeviceId, id);
  }
  
  // Auto sync
  Future<bool> getAutoSync() async {
    final prefs = await _prefs;
    return prefs.getBool(_keyAutoSync) ?? true;
  }
  
  Future<void> setAutoSync(bool value) async {
    final prefs = await _prefs;
    await prefs.setBool(_keyAutoSync, value);
  }
  
  // Confidence threshold
  Future<double> getConfidenceThreshold() async {
    final prefs = await _prefs;
    return prefs.getDouble(_keyConfidenceThreshold) ?? 0.7;
  }
  
  Future<void> setConfidenceThreshold(double value) async {
    final prefs = await _prefs;
    await prefs.setDouble(_keyConfidenceThreshold, value);
  }
  
  // Packages
  Future<List<PackageModel>> getPackages() async {
    final prefs = await _prefs;
    final json = prefs.getString(_keyPackages);
    if (json == null) return [];
    
    try {
      final list = jsonDecode(json) as List;
      return list.map((e) => PackageModel.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }
  
  Future<void> savePackages(List<PackageModel> packages) async {
    final prefs = await _prefs;
    final json = jsonEncode(packages.map((e) => e.toJson()).toList());
    await prefs.setString(_keyPackages, json);
  }
  
  // Pending sync
  Future<List<PackageModel>> getPendingSync() async {
    final prefs = await _prefs;
    final json = prefs.getString(_keyPendingSync);
    if (json == null) return [];
    
    try {
      final list = jsonDecode(json) as List;
      return list.map((e) => PackageModel.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }
  
  Future<void> savePendingSync(List<PackageModel> packages) async {
    final prefs = await _prefs;
    final json = jsonEncode(packages.map((e) => e.toJson()).toList());
    await prefs.setString(_keyPendingSync, json);
  }
}
