import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../providers/route_provider.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<RouteProvider>().loadRoutes();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      gradient: AppTheme.gradientGreen,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.local_shipping, color: Colors.white),
                  ),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Paket Driver',
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                      Text(
                        'Welcome back, Driver',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ],
              ),
              
              const SizedBox(height: 32),
              
              // Current Route Card
              Consumer<RouteProvider>(
                builder: (context, provider, child) {
                  if (provider.currentRoute != null) {
                    return _ActiveRouteCard(provider: provider);
                  }
                  return const SizedBox.shrink();
                },
              ),
              
              const SizedBox(height: 24),
              
              // Available Routes
              Text(
                'Available Routes',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              
              Expanded(
                child: Consumer<RouteProvider>(
                  builder: (context, provider, child) {
                    if (provider.isLoading) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    
                    if (provider.availableRoutes.isEmpty) {
                      return Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.route,
                              size: 64,
                              color: AppTheme.textMuted.withOpacity(0.5),
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'No routes available',
                              style: TextStyle(color: AppTheme.textMuted),
                            ),
                            const SizedBox(height: 24),
                            OutlinedButton.icon(
                              onPressed: () => provider.loadRoutes(),
                              icon: const Icon(Icons.refresh),
                              label: const Text('Refresh'),
                            ),
                          ],
                        ),
                      );
                    }
                    
                    return RefreshIndicator(
                      onRefresh: () => provider.loadRoutes(),
                      child: ListView.builder(
                        itemCount: provider.availableRoutes.length,
                        itemBuilder: (context, index) {
                          final route = provider.availableRoutes[index];
                          return _RouteCard(
                            vehicleId: route.vehicleId,
                            stops: route.stops.length,
                            distance: route.totalDistanceKm,
                            duration: route.totalTimeMinutes,
                            onTap: () {
                              provider.selectRoute(route);
                              Navigator.pushNamed(context, '/route');
                            },
                          );
                        },
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ActiveRouteCard extends StatelessWidget {
  final RouteProvider provider;
  
  const _ActiveRouteCard({required this.provider});
  
  @override
  Widget build(BuildContext context) {
    final route = provider.currentRoute!;
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AppTheme.gradientGreen,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppTheme.accentGreen.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.navigation, color: Colors.white),
              const SizedBox(width: 8),
              const Text(
                'Active Route',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
              ),
              const Spacer(),
              Text(
                route.vehicleId,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.8),
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // Progress
          Row(
            children: [
              Text(
                '${provider.completedStops}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                ' / ${provider.totalStops}',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 24,
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                'stops',
                style: TextStyle(color: Colors.white70),
              ),
            ],
          ),
          const SizedBox(height: 12),
          
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: provider.progressPercentage,
              backgroundColor: Colors.white24,
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 16),
          
          // Continue button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/route'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: AppTheme.accentGreen,
              ),
              child: const Text('Continue Route'),
            ),
          ),
        ],
      ),
    );
  }
}

class _RouteCard extends StatelessWidget {
  final String vehicleId;
  final int stops;
  final double distance;
  final int duration;
  final VoidCallback onTap;
  
  const _RouteCard({
    required this.vehicleId,
    required this.stops,
    required this.distance,
    required this.duration,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppTheme.accentBlue.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.route,
                  color: AppTheme.accentBlue,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      vehicleId,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$stops stops • ${distance.toStringAsFixed(1)} km • ${duration ~/ 60}h ${duration % 60}m',
                      style: const TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.chevron_right,
                color: AppTheme.textMuted,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
