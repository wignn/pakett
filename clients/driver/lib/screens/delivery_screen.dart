import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../providers/route_provider.dart';

class DeliveryScreen extends StatefulWidget {
  final int stopIndex;
  
  const DeliveryScreen({super.key, required this.stopIndex});

  @override
  State<DeliveryScreen> createState() => _DeliveryScreenState();
}

class _DeliveryScreenState extends State<DeliveryScreen> {
  String? _selectedReason;
  final _notesController = TextEditingController();
  
  final _skipReasons = [
    'Customer not home',
    'Wrong address',
    'Package refused',
    'Access restricted',
    'Other',
  ];
  
  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<RouteProvider>(
      builder: (context, provider, child) {
        final stop = provider.currentRoute?.stops[widget.stopIndex];
        
        if (stop == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Delivery')),
            body: const Center(child: Text('Stop not found')),
          );
        }
        
        return Scaffold(
          appBar: AppBar(
            title: Text('Stop #${stop.sequence}'),
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Address card
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppTheme.bgCard,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.borderPrimary),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.location_on, color: AppTheme.accentBlue),
                          const SizedBox(width: 12),
                          const Text(
                            'Delivery Address',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Text(
                        stop.addressSummary ?? 'Unknown Address',
                        style: const TextStyle(fontSize: 18),
                      ),
                      if (stop.packageId != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: AppTheme.accentBlue.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            stop.packageId!,
                            style: const TextStyle(
                              color: AppTheme.accentBlue,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Confirm Delivery
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () => _confirmDelivery(context, provider),
                    icon: const Icon(Icons.check_circle),
                    label: const Text('Confirm Delivery'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.accentGreen,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ),
                
                const SizedBox(height: 32),
                const Divider(color: AppTheme.borderPrimary),
                const SizedBox(height: 32),
                
                // Skip delivery section
                const Text(
                  'Unable to deliver?',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 16),
                
                // Reason dropdown
                DropdownButtonFormField<String>(
                  value: _selectedReason,
                  decoration: const InputDecoration(
                    labelText: 'Select reason',
                  ),
                  items: _skipReasons.map((reason) {
                    return DropdownMenuItem(
                      value: reason,
                      child: Text(reason),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      _selectedReason = value;
                    });
                  },
                ),
                
                const SizedBox(height: 16),
                
                // Notes
                TextField(
                  controller: _notesController,
                  decoration: const InputDecoration(
                    labelText: 'Additional notes (optional)',
                    hintText: 'Add any relevant details...',
                  ),
                  maxLines: 3,
                ),
                
                const SizedBox(height: 24),
                
                // Skip button
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _selectedReason == null
                        ? null
                        : () => _skipDelivery(context, provider),
                    icon: const Icon(Icons.skip_next),
                    label: const Text('Skip This Stop'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.accentOrange,
                      side: const BorderSide(color: AppTheme.accentOrange),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
  
  void _confirmDelivery(BuildContext context, RouteProvider provider) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: const Text('Confirm Delivery'),
        content: const Text('Mark this package as delivered?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              provider.completeCurrentStop();
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Back to route
              
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Delivery confirmed!'),
                  backgroundColor: AppTheme.accentGreen,
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.accentGreen,
            ),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
  
  void _skipDelivery(BuildContext context, RouteProvider provider) {
    final reason = _selectedReason ?? '';
    final notes = _notesController.text.isNotEmpty
        ? '$reason: ${_notesController.text}'
        : reason;
    
    provider.skipCurrentStop(notes);
    Navigator.pop(context);
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Stop skipped'),
        backgroundColor: AppTheme.accentOrange,
      ),
    );
  }
}
