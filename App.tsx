/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */

import './src/third-party/i18n/i18n';

import { BottomSheetModalProvider } from '@gorhom/bottom-sheet';
import { NewAppScreen } from '@react-native/new-app-screen';
import { View } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import {
  SafeAreaProvider,
  useSafeAreaInsets,
} from 'react-native-safe-area-context';
import { ThemedNavigationContainer } from './src/navigation/ThemedNavigationContainer';
import { QueryProvider } from './src/query/QueryProvider';
import { AppThemeProvider } from './src/theme/ThemeContext';
import { useThemedStyles } from './src/theme/useThemedStyles';
import { ConnectivityProvider } from './src/connectivity/ConnectivityHelper';
import { FeedbackProvider } from './src/feedback';

function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <BottomSheetModalProvider>
        <SafeAreaProvider>
          <FeedbackProvider>
            <QueryProvider>
              <AppThemeProvider>
                <ConnectivityProvider>
                  <ThemedNavigationContainer />
                </ConnectivityProvider>
              </AppThemeProvider>
            </QueryProvider>
          </FeedbackProvider>
        </SafeAreaProvider>
      </BottomSheetModalProvider>
    </GestureHandlerRootView>
  );
}

function AppContent() {
  const safeAreaInsets = useSafeAreaInsets();
  const styles = useThemedStyles(colors => ({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
  }));

  return (
    <View style={styles.container}>
      <NewAppScreen
        templateFileName="App.tsx"
        safeAreaInsets={safeAreaInsets}
      />
    </View>
  );
}

export { AppContent };
export default App;
