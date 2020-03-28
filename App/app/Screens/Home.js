import React from "react";
import { Text, StyleSheet, View, Button } from "react-native";
//import axios from 'axios';


class Home extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      btnMessage: 'READ ECG',
      isReading: false,
      totalSecondsForRound: 0
    };
  }

  activityClicked = () => { }/*
    //If we are currently reading data, stop reading
    if(this.state.isReading){
      this.setState({
        btnMessage: 'READ ECG',
        isReading: false
      })
      //Stop executing the method with the timer
      clearInterval(sender);
      this.sendData(data); //Send the remaining data
    }
    //If off, start reading data, and passing it in to the controller
    else{
      var data = []; //This array will hold the data to be passed
      this.setState({
        btnMessage: 'STOP READING',
        isReading: true
      })

      //This function is being executed every 300 seconds (5 minutes), and it passes the data that has been 
      //collected in those five minutes to the backend
      var sender = setInterval(sendData, 300000);
      //So long as we are reading
      while(this.state.isReading){
        this.gatherData();
      }
    }
  }
  //This function sends data into the controller
  sendData = (data) => {
    //Here we will have to replace the path with the correct path to the controller that will handle the request
    axios.post(`https://jsonplaceholder.typicode.com/users`, data)
    .then(res => {
      console.log(res);
      console.log(res.data);
    })

  }
  //This function add data to the data array, as we go
  gatherData = () => {
    let d = dataGenerator();//Get delay between pulses
    //If we are not sending the data at this moment
    data.push(d);//Add to the data array
    wait(d * 1000);//Pause for that duration, to simulate the delay
  }
  //For testing, generate some data
  dataGenerator = () => {
    //Generate number between 0 and 300.
    let n = Math.floor(Math.random() * 301);
    //divide 60 by the number, to get the amount of seconds that there is delay
    return 60 / n ;
  }
*/
  render(){
    const { params } = this.props.navigation.state;
    return (
        <View style={{
            backgroundColor: "#ffaf9e", height: "100%", flex: 1,
            alignItems: 'center',
            justifyContent: 'center'}}>
            <Text style={styles.text}>Welcome to ECG Analysis</Text>
            <Button title={this.state.btnMessage} color="#ff7152" onPress={() => this.activityClicked()}/>
            <Button title='Logout' onPress={() =>{
                  params.onLogout();
            }} />
        </View>
        )
  }
};

const styles = StyleSheet.create({
  text: {
    fontSize: 30
  }
});

export default Home;
