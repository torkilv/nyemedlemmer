import React, { Component } from 'react';
import './App.css';
import axios from 'axios';
import distanceInWordsToNow  from 'date-fns/distance_in_words_to_now';
import differenceInMinutes from 'date-fns/difference_in_minutes';
import nblocale from 'date-fns/locale/nb';
import bikebell from './bikebell.mp3';
import arildBilde from './arild.jpeg';

class App extends Component {

  state = {
    new_members: []
  };

  getItems() {
    axios
    .get("http://0.0.0.0:5000")
    .then( response =>  {
        const newState = {new_members: response.data};
        this.setState(newState);
    })
    .catch(error => console.log(error));
  }

  componentDidMount() {
    this.timer = setInterval(() => this.getItems(), 180000);
    this.getItems();
  }

  componentWillUnmount() {
    this.timer = null; 
  }

  defaultPage() {
    return (
      <div className="App"><h1>STÅ PÅ, MILJØHELTER!</h1>
        <img alt="Arild på sykkel" src={arildBilde} />
      </div>);
  }

  createListItemForMember(member, i) {
    const signedUpDate = new Date(member.timestamp*1000);

    const timeSinceWords = "for "+distanceInWordsToNow(signedUpDate, {locale: nblocale}) + " siden";
    const minutesSince = differenceInMinutes(new Date(), signedUpDate);
    
    const myRef = React.createRef();

    return <li key={i} className={minutesSince < 60 ? "new" : undefined}>
              <div className={"chapter"}>{member.chapter} </div>
              <div className="time"> {timeSinceWords}</div> 
              {minutesSince < 3 && <audio ref={myRef} src={bikebell} autoPlay/>}
            </li>
  }

  render() {

    if (this.state.new_members.length < 2) {
      return this.defaultPage();
    }

    return (
    <div className="App">
      <h1>NYE MEDLEMMER DET SISTE DØGNET: {this.state.new_members.length} </h1>
      
      <h2>Gratulerer med nytt medlem til:</h2>
   
      <ul>
        {this.state.new_members.map(this.createListItemForMember)}
      </ul>
    </div>  
    );
  }
}

export default App;
