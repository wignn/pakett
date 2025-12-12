class PackageModel {
  final String id;
  final String packageId;
  final String deviceId;
  final String ocrText;
  final double ocrConfidence;
  final String status;
  final String priority;
  final DateTime createdAt;
  final double? lat;
  final double? lon;
  final ParsedAddress? address;
  
  PackageModel({
    required this.id,
    required this.packageId,
    required this.deviceId,
    required this.ocrText,
    required this.ocrConfidence,
    required this.status,
    required this.priority,
    required this.createdAt,
    this.lat,
    this.lon,
    this.address,
  });
  
  factory PackageModel.fromJson(Map<String, dynamic> json) {
    return PackageModel(
      id: json['id'] ?? '',
      packageId: json['package_id'] ?? '',
      deviceId: json['device_id'] ?? '',
      ocrText: json['ocr_text'] ?? '',
      ocrConfidence: (json['ocr_confidence'] ?? 0).toDouble(),
      status: json['status'] ?? 'pending',
      priority: json['priority'] ?? 'standard',
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
      lat: json['lat']?.toDouble(),
      lon: json['lon']?.toDouble(),
      address: json['parsed_address'] != null 
          ? ParsedAddress.fromJson(json['parsed_address'])
          : null,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'package_id': packageId,
      'device_id': deviceId,
      'ocr_text': ocrText,
      'ocr_confidence': ocrConfidence,
      'status': status,
      'priority': priority,
      'created_at': createdAt.toIso8601String(),
      'lat': lat,
      'lon': lon,
    };
  }
  
  Map<String, dynamic> toIngestRequest() {
    final request = <String, dynamic>{
      'device_id': deviceId,
      'package_id': packageId,
      'ocr_text': ocrText,
      'ocr_confidence': ocrConfidence,
      'priority': priority,
    };
    
    if (lat != null && lon != null) {
      request['gps'] = {'lat': lat, 'lon': lon};
    }
    
    return request;
  }
}

class ParsedAddress {
  final String? street;
  final String? houseNumber;
  final String? rt;
  final String? rw;
  final String? subdistrict;
  final String? city;
  final String? postalCode;
  final double confidence;
  
  ParsedAddress({
    this.street,
    this.houseNumber,
    this.rt,
    this.rw,
    this.subdistrict,
    this.city,
    this.postalCode,
    this.confidence = 0,
  });
  
  factory ParsedAddress.fromJson(Map<String, dynamic> json) {
    return ParsedAddress(
      street: json['street'],
      houseNumber: json['house_number'],
      rt: json['rt'],
      rw: json['rw'],
      subdistrict: json['subdistrict'],
      city: json['city'],
      postalCode: json['postal_code'],
      confidence: (json['confidence'] ?? 0).toDouble(),
    );
  }
  
  String get formatted {
    final parts = <String>[];
    if (street != null) parts.add('$street ${houseNumber ?? ''}');
    if (rt != null || rw != null) parts.add('RT ${rt ?? '-'}/RW ${rw ?? '-'}');
    if (subdistrict != null) parts.add(subdistrict!);
    if (city != null) parts.add(city!);
    if (postalCode != null) parts.add(postalCode!);
    return parts.join(', ');
  }
}
