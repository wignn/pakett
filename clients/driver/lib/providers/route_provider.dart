import 'package:flutter/material.dart';
import '../models/route_model.dart';
import '../services/api_service.dart';

class RouteProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  
  RouteModel? _currentRoute;
  List<RouteModel> _availableRoutes = [];
  bool _isLoading = false;
  String? _error;
  int _currentStopIndex = 0;
  
  RouteModel? get currentRoute => _currentRoute;
  List<RouteModel> get availableRoutes => _availableRoutes;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get currentStopIndex => _currentStopIndex;
  
  RouteStop? get currentStop {
    if (_currentRoute == null || 
        _currentStopIndex >= _currentRoute!.stops.length) {
      return null;
    }
    return _currentRoute!.stops[_currentStopIndex];
  }
  
  RouteStop? get nextStop {
    if (_currentRoute == null || 
        _currentStopIndex + 1 >= _currentRoute!.stops.length) {
      return null;
    }
    return _currentRoute!.stops[_currentStopIndex + 1];
  }
  
  int get completedStops {
    if (_currentRoute == null) return 0;
    return _currentRoute!.stops
        .where((s) => s.status == 'completed')
        .length;
  }
  
  int get totalStops {
    return _currentRoute?.stops.length ?? 0;
  }
  
  double get progressPercentage {
    if (totalStops == 0) return 0;
    return completedStops / totalStops;
  }
  
  Future<void> loadRoutes() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      _availableRoutes = await _api.getRoutes();
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> selectRoute(RouteModel route) async {
    _currentRoute = route;
    _currentStopIndex = 0;
    
    // Find first non-completed stop
    for (int i = 0; i < route.stops.length; i++) {
      if (route.stops[i].status != 'completed') {
        _currentStopIndex = i;
        break;
      }
    }
    
    notifyListeners();
  }
  
  Future<void> completeCurrentStop() async {
    if (_currentRoute == null || currentStop == null) return;
    
    _isLoading = true;
    notifyListeners();
    
    try {
      // Update stop status
      _currentRoute!.stops[_currentStopIndex] = currentStop!.copyWith(
        status: 'completed',
        actualArrival: DateTime.now(),
      );
      
      // Move to next stop
      if (_currentStopIndex < _currentRoute!.stops.length - 1) {
        _currentStopIndex++;
      }
      
      notifyListeners();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> skipCurrentStop(String reason) async {
    if (_currentRoute == null || currentStop == null) return;
    
    _currentRoute!.stops[_currentStopIndex] = currentStop!.copyWith(
      status: 'skipped',
      notes: reason,
    );
    
    if (_currentStopIndex < _currentRoute!.stops.length - 1) {
      _currentStopIndex++;
    }
    
    notifyListeners();
  }
  
  void clearRoute() {
    _currentRoute = null;
    _currentStopIndex = 0;
    notifyListeners();
  }
}
