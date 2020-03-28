import { createAppContainer } from 'react-navigation';
import { createStackNavigator } from 'react-navigation-stack';
import Login from './Screens/Login';
import Home from './Screens/Home';

const navigator = createStackNavigator(
  {
    Login: { screen: Login },
    Home: { screen: Home }
  },
  {
    initialRouteName: "Login",
    headerMode: 'none'
  }
);

export default createAppContainer(navigator);
