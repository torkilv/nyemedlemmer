import React, { Component } from 'react';
import './App.css';
import axios from 'axios';
import distanceInWordsToNow  from 'date-fns/distance_in_words_to_now';
import differenceInMinutes from 'date-fns/difference_in_minutes';
import nblocale from 'date-fns/locale/nb';
import bikebell from './bikebell.mp3';
import Sound from 'react-sound';
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
    this.timer = setInterval(()=> this.getItems(), 180000);
    this.getItems();

  }

  componentWillUnmount() {
  this.timer = null; // here...
  }

  render() {
    const render_State = this.state.new_members.map(function(member) {
      const signedUpDate = new Date(member.timestamp*1000);

      return {chapter: member.chapter,
              timeSince: distanceInWordsToNow(signedUpDate, {locale: nblocale}),
              minutesSince: differenceInMinutes(new Date(), signedUpDate)}
    });
    if (render_State.length < 2) {
      return (<div className="App"><h1>STÅ PÅ, MILJØHELTER!</h1>
        <img src={arildBilde} />

        </div>)
    }

    const newMemberNow = render_State[0].minutesSince < 3;
      

    return (
      <div className="App">
      <h1>NYE MEDLEMMER DET SISTE DØGNET: {this.state.new_members.length} </h1>
      {newMemberNow && <Sound
   url={bikebell}
   playStatus={Sound.status.PLAYING}
   onLoading={this.handleSongLoading}
   onPlaying={this.handleSongPlaying}
   onFinishedPlaying={this.handleSongFinishedPlaying}
   />} 
   <h2>Gratulerer med nytt medlem til:</h2>
      <ul >

      {render_State.map(function(member, i) {
        return <li key={i} className={member.minutesSince < 60 ? "new" : undefined}><div className={"chapter"}>{member.chapter}</div><div className="time"> for {member.timeSince} siden</div> </li>
      })}
        
      </ul>
      </div>
      
    );
  }
}

export default App;
