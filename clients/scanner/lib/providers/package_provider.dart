import 'package:flutter/material.dart';
import '../models/package_model.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

class PackageProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  final StorageService _storage = StorageService();
  
  List<PackageModel> _packages = [];
  List<PackageModel> _pendingSync = [];
  bool _isLoading = false;
  String? _error;
  
  List<PackageModel> get packages => _packages;
  List<PackageModel> get pendingSync => _pendingSync;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get pendingSyncCount => _pendingSync.length;
  
  PackageProvider() {
    _loadFromStorage();
  }
  
  Future<void> _loadFromStorage() async {
    _packages = await _storage.getPackages();
    _pendingSync = await _storage.getPendingSync();
    notifyListeners();
  }
  
  Future<PackageModel?> ingestPackage({
    required String packageId,
    required String ocrText,
    required double ocrConfidence,
    double? lat,
    double? lon,
    String priority = 'standard',
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    final package = PackageModel(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      packageId: packageId,
      deviceId: await _storage.getDeviceId(),
      ocrText: ocrText,
      ocrConfidence: ocrConfidence,
      status: 'pending',
      priority: priority,
      createdAt: DateTime.now(),
      lat: lat,
      lon: lon,
    );
    
    try {
      // Try to send to server
      final result = await _api.ingestPackage(package);
      
      if (result != null) {
        // Success - update with server response
        _packages.insert(0, result);
        await _storage.savePackages(_packages);
        notifyListeners();
        return result;
      } else {
        // Failed - save for later sync
        _pendingSync.add(package);
        await _storage.savePendingSync(_pendingSync);
        _packages.insert(0, package);
        await _storage.savePackages(_packages);
        notifyListeners();
        return package;
      }
    } catch (e) {
      // Offline - save for later sync
      _error = e.toString();
      _pendingSync.add(package);
      await _storage.savePendingSync(_pendingSync);
      _packages.insert(0, package);
      await _storage.savePackages(_packages);
      notifyListeners();
      return package;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> syncPending() async {
    if (_pendingSync.isEmpty) return;
    
    _isLoading = true;
    notifyListeners();
    
    final toSync = List<PackageModel>.from(_pendingSync);
    final synced = <PackageModel>[];
    
    for (final package in toSync) {
      try {
        final result = await _api.ingestPackage(package);
        if (result != null) {
          synced.add(package);
          // Update in packages list
          final index = _packages.indexWhere((p) => p.id == package.id);
          if (index >= 0) {
            _packages[index] = result;
          }
        }
      } catch (e) {
        // Skip failed ones
      }
    }
    
    // Remove synced from pending
    _pendingSync.removeWhere((p) => synced.any((s) => s.id == p.id));
    await _storage.savePendingSync(_pendingSync);
    await _storage.savePackages(_packages);
    
    _isLoading = false;
    notifyListeners();
  }
  
  Future<void> clearHistory() async {
    _packages.clear();
    await _storage.savePackages(_packages);
    notifyListeners();
  }
}
