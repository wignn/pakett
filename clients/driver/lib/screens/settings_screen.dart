import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/storage_service.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final StorageService _storage = StorageService();
  final ApiService _api = ApiService();
  final _serverUrlController = TextEditingController();
  final _driverNameController = TextEditingController();
  final _vehicleIdController = TextEditingController();
  bool _isLoading = true;
  bool _isSaving = false;
  bool _isConnected = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final serverUrl = await _storage.getServerUrl();
    final driverName = await _storage.getDriverName();
    final vehicleId = await _storage.getVehicleId();
    
    setState(() {
      _serverUrlController.text = serverUrl;
      _driverNameController.text = driverName ?? '';
      _vehicleIdController.text = vehicleId ?? '';
      _isLoading = false;
    });
    
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    final isConnected = await _api.checkHealth();
    setState(() => _isConnected = isConnected);
  }

  Future<void> _saveSettings() async {
    setState(() => _isSaving = true);
    
    await _storage.setServerUrl(_serverUrlController.text.trim());
    await _storage.setDriverName(_driverNameController.text.trim());
    await _storage.setVehicleId(_vehicleIdController.text.trim());
    
    await _checkConnection();
    
    setState(() => _isSaving = false);
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_isConnected ? 'Settings saved successfully!' : 'Settings saved, but server is not reachable'),
          backgroundColor: _isConnected ? AppTheme.accentGreen : AppTheme.accentOrange,
        ),
      );
    }
  }

  @override
  void dispose() {
    _serverUrlController.dispose();
    _driverNameController.dispose();
    _vehicleIdController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Connection Status
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: _isConnected
                          ? AppTheme.accentGreen.withOpacity(0.1)
                          : AppTheme.accentRed.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: _isConnected ? AppTheme.accentGreen : AppTheme.accentRed,
                        width: 1,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _isConnected ? Icons.cloud_done : Icons.cloud_off,
                          color: _isConnected ? AppTheme.accentGreen : AppTheme.accentRed,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            _isConnected ? 'Connected to server' : 'Not connected',
                            style: TextStyle(
                              color: _isConnected ? AppTheme.accentGreen : AppTheme.accentRed,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        TextButton(
                          onPressed: _checkConnection,
                          child: const Text('Test'),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Server Settings
                  Text(
                    'Server Settings',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  TextField(
                    controller: _serverUrlController,
                    decoration: const InputDecoration(
                      labelText: 'Server URL',
                      hintText: 'http://192.168.1.100:8001',
                      prefixIcon: Icon(Icons.dns),
                    ),
                    keyboardType: TextInputType.url,
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Driver Info
                  Text(
                    'Driver Information',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  TextField(
                    controller: _driverNameController,
                    decoration: const InputDecoration(
                      labelText: 'Driver Name',
                      hintText: 'John Doe',
                      prefixIcon: Icon(Icons.person),
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  TextField(
                    controller: _vehicleIdController,
                    decoration: const InputDecoration(
                      labelText: 'Vehicle ID',
                      hintText: 'V001',
                      prefixIcon: Icon(Icons.local_shipping),
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Save Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _isSaving ? null : _saveSettings,
                      icon: _isSaving
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.save),
                      label: Text(_isSaving ? 'Saving...' : 'Save Settings'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.accentGreen,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
