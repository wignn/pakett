import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'screens/home_screen.dart';
import 'screens/route_screen.dart';
import 'screens/delivery_screen.dart';
import 'screens/settings_screen.dart';
import 'providers/route_provider.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  
  runApp(const PaketDriverApp());
}

class PaketDriverApp extends StatelessWidget {
  const PaketDriverApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => RouteProvider()),
      ],
      child: MaterialApp(
        title: 'Paket Driver',
        theme: AppTheme.darkTheme,
        debugShowCheckedModeBanner: false,
        initialRoute: '/',
        routes: {
          '/': (context) => const HomeScreen(),
          '/route': (context) => const RouteScreen(),
          '/settings': (context) => const SettingsScreen(),
        },
        onGenerateRoute: (settings) {
          if (settings.name == '/delivery') {
            final stopIndex = settings.arguments as int;
            return MaterialPageRoute(
              builder: (context) => DeliveryScreen(stopIndex: stopIndex),
            );
          }
          return null;
        },
      ),
    );
  }
}
