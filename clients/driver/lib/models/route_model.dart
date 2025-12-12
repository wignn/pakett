class RouteModel {
  final String id;
  final String vehicleId;
  final String? driverName;
  final DateTime plannedDate;
  final String status;
  final double totalDistanceKm;
  final int totalTimeMinutes;
  final List<RouteStop> stops;
  
  RouteModel({
    required this.id,
    required this.vehicleId,
    this.driverName,
    required this.plannedDate,
    required this.status,
    required this.totalDistanceKm,
    required this.totalTimeMinutes,
    required this.stops,
  });
  
  factory RouteModel.fromJson(Map<String, dynamic> json) {
    return RouteModel(
      id: json['id'] ?? '',
      vehicleId: json['vehicle_id'] ?? json['vehicle_code'] ?? '',
      driverName: json['driver_name'],
      plannedDate: DateTime.tryParse(json['planned_date'] ?? '') ?? DateTime.now(),
      status: json['status'] ?? 'planned',
      totalDistanceKm: (json['total_distance_km'] ?? 0).toDouble(),
      totalTimeMinutes: json['total_time_minutes'] ?? 0,
      stops: (json['stops'] as List?)
          ?.map((e) => RouteStop.fromJson(e))
          .toList() ?? [],
    );
  }
}

class RouteStop {
  final String? id;
  final int sequence;
  final String? packageId;
  final double lat;
  final double lon;
  final String? addressSummary;
  final DateTime? estimatedArrival;
  final DateTime? actualArrival;
  final String status;
  final String? notes;
  
  RouteStop({
    this.id,
    required this.sequence,
    this.packageId,
    required this.lat,
    required this.lon,
    this.addressSummary,
    this.estimatedArrival,
    this.actualArrival,
    this.status = 'pending',
    this.notes,
  });
  
  factory RouteStop.fromJson(Map<String, dynamic> json) {
    return RouteStop(
      id: json['id'],
      sequence: json['sequence'] ?? json['sequence_order'] ?? 0,
      packageId: json['package_id'],
      lat: (json['lat'] ?? 0).toDouble(),
      lon: (json['lon'] ?? 0).toDouble(),
      addressSummary: json['address_summary'],
      estimatedArrival: json['estimated_arrival'] != null
          ? DateTime.tryParse(json['estimated_arrival'])
          : null,
      actualArrival: json['actual_arrival'] != null
          ? DateTime.tryParse(json['actual_arrival'])
          : null,
      status: json['status'] ?? 'pending',
      notes: json['notes'],
    );
  }
  
  RouteStop copyWith({
    String? status,
    DateTime? actualArrival,
    String? notes,
  }) {
    return RouteStop(
      id: id,
      sequence: sequence,
      packageId: packageId,
      lat: lat,
      lon: lon,
      addressSummary: addressSummary,
      estimatedArrival: estimatedArrival,
      actualArrival: actualArrival ?? this.actualArrival,
      status: status ?? this.status,
      notes: notes ?? this.notes,
    );
  }
  
  bool get isDepot => sequence == 0;
  bool get isCompleted => status == 'completed';
  bool get isPending => status == 'pending';
}
