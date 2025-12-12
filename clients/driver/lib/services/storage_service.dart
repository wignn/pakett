import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const String _keyServerUrl = 'server_url';
  static const String _keyDriverId = 'driver_id';
  static const String _keyDriverName = 'driver_name';
  static const String _keyVehicleId = 'vehicle_id';
  
  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();
  
  // Server URL
  Future<String> getServerUrl() async {
    final prefs = await _prefs;
    return prefs.getString(_keyServerUrl) ?? 'http://208.76.40.118:8001';
  }
  
  Future<void> setServerUrl(String url) async {
    final prefs = await _prefs;
    await prefs.setString(_keyServerUrl, url);
  }
  
  // Driver ID
  Future<String?> getDriverId() async {
    final prefs = await _prefs;
    return prefs.getString(_keyDriverId);
  }
  
  Future<void> setDriverId(String id) async {
    final prefs = await _prefs;
    await prefs.setString(_keyDriverId, id);
  }
  
  // Driver Name
  Future<String?> getDriverName() async {
    final prefs = await _prefs;
    return prefs.getString(_keyDriverName);
  }
  
  Future<void> setDriverName(String name) async {
    final prefs = await _prefs;
    await prefs.setString(_keyDriverName, name);
  }
  
  // Vehicle ID
  Future<String?> getVehicleId() async {
    final prefs = await _prefs;
    return prefs.getString(_keyVehicleId);
  }
  
  Future<void> setVehicleId(String id) async {
    final prefs = await _prefs;
    await prefs.setString(_keyVehicleId, id);
  }
  
  // Clear all settings
  Future<void> clearAll() async {
    final prefs = await _prefs;
    await prefs.clear();
  }
}
