import React, { Component } from 'react';
import { Text, StyleSheet, View } from "react-native";
//import Auth0 from 'react-native-auth0';

//var credentials = require('./auth0-configuration');
//const auth0 = new Auth0(credentials);

/*const LoginScreen = () => {
  return <Text style={styles.text}>Login Page!</Text>;
};

const styles = StyleSheet.create({
  text: {
    fontSize: 30
  }
});
*/

class LoginScreen extends Component {
    constructor(props) {
        super(props);
        this.state = { accessToken: null };
    }

    render() {
        return (
        <View style = { styles.container }>
            <Text style = { styles.header }> Login Page! </Text>
        </View >
        );
    }
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#F5FCFF'
    },
    text: {
        fontSize: 30
    }
});

export default LoginScreen;
