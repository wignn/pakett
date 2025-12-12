import 'package:flutter/material.dart';
import '../services/storage_service.dart';

class SettingsProvider extends ChangeNotifier {
  final StorageService _storage = StorageService();
  
  String _serverUrl = 'http://localhost:8000';
  String _deviceId = '';
  bool _autoSync = true;
  double _confidenceThreshold = 0.7;
  
  String get serverUrl => _serverUrl;
  String get deviceId => _deviceId;
  bool get autoSync => _autoSync;
  double get confidenceThreshold => _confidenceThreshold;
  
  SettingsProvider() {
    _loadSettings();
  }
  
  Future<void> _loadSettings() async {
    _serverUrl = await _storage.getServerUrl();
    _deviceId = await _storage.getDeviceId();
    _autoSync = await _storage.getAutoSync();
    _confidenceThreshold = await _storage.getConfidenceThreshold();
    notifyListeners();
  }
  
  Future<void> setServerUrl(String url) async {
    _serverUrl = url;
    await _storage.setServerUrl(url);
    notifyListeners();
  }
  
  Future<void> setDeviceId(String id) async {
    _deviceId = id;
    await _storage.setDeviceId(id);
    notifyListeners();
  }
  
  Future<void> setAutoSync(bool value) async {
    _autoSync = value;
    await _storage.setAutoSync(value);
    notifyListeners();
  }
  
  Future<void> setConfidenceThreshold(double value) async {
    _confidenceThreshold = value;
    await _storage.setConfidenceThreshold(value);
    notifyListeners();
  }
}
