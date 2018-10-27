import React, { Component } from 'react';
import './NewMemberList.css';
import axios from 'axios';
import distanceInWordsToNow  from 'date-fns/distance_in_words_to_now';
import differenceInMinutes from 'date-fns/difference_in_minutes';
import nblocale from 'date-fns/locale/nb';
import bikebell from './bikebell.mp3';
import arildBilde from './arild.jpeg';

var API_GET_NEW_MEMBERS_URL = "http://0.0.0.0:5000"
var NOTIFICATION_TRESHOLD_MINUTES = 3
var HILIGHT_TRESHOLD_MINUTES = 60
var SHOWN_DAYS_TRESHOLD = 0

class NewMemberList extends Component {

  state = {
    new_members: []
  };

  getItems() {
    axios
    .get(API_GET_NEW_MEMBERS_URL+"/" + SHOWN_DAYS_TRESHOLD)
    .then( response =>  {
        const newState = {new_members: response.data};
        this.setState(newState);
    })
    .catch(error => console.log(error));
  }

  componentDidMount() {
    this.timer = setInterval(() => this.getItems(), NOTIFICATION_TRESHOLD_MINUTES * 60 * 1000);
    this.getItems();
  }

  componentWillUnmount() {
    this.timer = null;
  }

  defaultPage() {
    return (
      <div className="NewMemberList"><h1>STÅ PÅ, MILJØHELTER!</h1>
        <img alt="Arild på sykkel" src={arildBilde} />
      </div>);
  }

  createListItemForMember(member, i) {
    const signedUpTime = new Date(member.timestamp);

    const timeSinceWords = "for "+distanceInWordsToNow(signedUpTime, {locale: nblocale}) + " siden";
    const minutesSince = differenceInMinutes(new Date(), signedUpTime);
    
    const myRef = React.createRef();

    return <li key={i} className={minutesSince < HILIGHT_TRESHOLD_MINUTES ? "new" : undefined}>
              <div className={"chapter"}>{member.chapter} </div>
              <div className="time"> {timeSinceWords}</div>
              {minutesSince < HILIGHT_TRESHOLD_MINUTES && 
                <audio ref={myRef} src={bikebell} autoPlay/>}
            </li>
  }

  render() {

    if (this.state.new_members.length < 2) {
      return this.defaultPage();
    }

    return (
    <div className="NewMemberList">
      <h1>NYE MEDLEMMER DET SISTE DØGNET: {this.state.new_members.length} </h1>

      <h2>Gratulerer med nytt medlem til:</h2>

      <ul>
        {this.state.new_members.map(this.createListItemForMember)}
      </ul>
    </div>
    );
  }
}


export default NewMemberList;