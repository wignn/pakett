import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../providers/route_provider.dart';
import '../models/route_model.dart';

class RouteScreen extends StatelessWidget {
  const RouteScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<RouteProvider>(
      builder: (context, provider, child) {
        if (provider.currentRoute == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Route')),
            body: const Center(child: Text('No route selected')),
          );
        }
        
        final route = provider.currentRoute!;
        final currentStop = provider.currentStop;
        
        return Scaffold(
          body: Stack(
            children: [
              // Map
              FlutterMap(
                options: MapOptions(
                  initialCenter: currentStop != null
                      ? LatLng(currentStop.lat, currentStop.lon)
                      : const LatLng(-6.2088, 106.8456),
                  initialZoom: 14,
                ),
                children: [
                  TileLayer(
                    urlTemplate: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                    subdomains: const ['a', 'b', 'c', 'd'],
                  ),
                  
                  // Route line
                  PolylineLayer(
                    polylines: [
                      Polyline(
                        points: route.stops
                            .map((s) => LatLng(s.lat, s.lon))
                            .toList(),
                        color: AppTheme.accentBlue,
                        strokeWidth: 4,
                        isDotted: true,
                      ),
                    ],
                  ),
                  
                  // Stop markers
                  MarkerLayer(
                    markers: route.stops.asMap().entries.map((entry) {
                      final index = entry.key;
                      final stop = entry.value;
                      final isCurrent = index == provider.currentStopIndex;
                      
                      Color markerColor;
                      if (stop.isCompleted) {
                        markerColor = AppTheme.accentGreen;
                      } else if (isCurrent) {
                        markerColor = AppTheme.accentOrange;
                      } else {
                        markerColor = AppTheme.accentBlue;
                      }
                      
                      return Marker(
                        point: LatLng(stop.lat, stop.lon),
                        width: isCurrent ? 50 : 36,
                        height: isCurrent ? 50 : 36,
                        child: Container(
                          decoration: BoxDecoration(
                            color: markerColor,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 3),
                            boxShadow: isCurrent
                                ? [
                                    BoxShadow(
                                      color: markerColor.withOpacity(0.5),
                                      blurRadius: 15,
                                    ),
                                  ]
                                : null,
                          ),
                          child: Center(
                            child: stop.isDepot
                                ? const Icon(Icons.home, color: Colors.white, size: 18)
                                : Text(
                                    '${stop.sequence}',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w700,
                                      fontSize: 14,
                                    ),
                                  ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
              
              // Top bar
              SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      IconButton.filled(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.arrow_back),
                        style: IconButton.styleFrom(
                          backgroundColor: AppTheme.bgCard,
                        ),
                      ),
                      const Spacer(),
                      // Progress chip
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.bgCard,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppTheme.borderPrimary),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.check_circle,
                              color: AppTheme.accentGreen,
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '${provider.completedStops}/${provider.totalStops}',
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              
              // Bottom panel
              Positioned(
                left: 0,
                right: 0,
                bottom: 0,
                child: _BottomPanel(
                  provider: provider,
                  currentStop: currentStop,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _BottomPanel extends StatelessWidget {
  final RouteProvider provider;
  final RouteStop? currentStop;
  
  const _BottomPanel({
    required this.provider,
    required this.currentStop,
  });
  
  @override
  Widget build(BuildContext context) {
    if (currentStop == null) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: const BoxDecoration(
          color: AppTheme.bgCard,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.check_circle,
              color: AppTheme.accentGreen,
              size: 64,
            ),
            const SizedBox(height: 16),
            const Text(
              'Route Complete!',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'All ${provider.totalStops} stops delivered',
              style: const TextStyle(color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  provider.clearRoute();
                  Navigator.popUntil(context, (route) => route.isFirst);
                },
                child: const Text('Back to Home'),
              ),
            ),
          ],
        ),
      );
    }
    
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 20,
            offset: Offset(0, -5),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppTheme.borderPrimary,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),
          
          // Stop info
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppTheme.accentOrange,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Center(
                  child: Text(
                    '${currentStop?.sequence ?? ''}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      fontSize: 18,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      currentStop?.addressSummary ?? 'Unknown Address',
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 16,
                      ),
                    ),
                    if (currentStop?.packageId != null)
                      Text(
                        currentStop!.packageId!,
                        style: const TextStyle(
                          color: AppTheme.textMuted,
                          fontSize: 13,
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          
          // Actions
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _openNavigation(context, currentStop!),
                  icon: const Icon(Icons.navigation),
                  label: const Text('Navigate'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: ElevatedButton.icon(
                  onPressed: provider.isLoading
                      ? null
                      : () => Navigator.pushNamed(
                            context,
                            '/delivery',
                            arguments: provider.currentStopIndex,
                          ),
                  icon: const Icon(Icons.check),
                  label: const Text('Complete Delivery'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.accentGreen,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          
          // Next stop preview
          if (provider.nextStop != null) ...[
            const Divider(color: AppTheme.borderPrimary),
            const SizedBox(height: 8),
            Row(
              children: [
                const Text(
                  'Next:',
                  style: TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    provider.nextStop!.addressSummary ?? 'Unknown',
                    style: const TextStyle(fontSize: 13),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
  
  void _openNavigation(BuildContext context, RouteStop stop) async {
    final url = 'https://www.google.com/maps/dir/?api=1&destination=${stop.lat},${stop.lon}';
    if (await canLaunchUrl(Uri.parse(url))) {
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    }
  }
}
