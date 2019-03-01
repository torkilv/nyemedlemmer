import React, { Component } from 'react';
import './NewMemberList.css';
import axios from 'axios';
import distanceInWordsToNow  from 'date-fns/distance_in_words_to_now';
import distanceInWords from 'date-fns/distance_in_words';
import differenceInMinutes from 'date-fns/difference_in_minutes';
import nblocale from 'date-fns/locale/nb';
import bikebell from './bikebell.mp3';
import arildBilde from './arild.jpeg';

var API_GET_NEW_MEMBERS_URL = "http://0.0.0.0:5000/newmembers"
var API_GET_LISTS_URL = "http://0.0.0.0:5000/lists"
var NOTIFICATION_TRESHOLD_MINUTES = 3
var HILIGHT_TRESHOLD_MINUTES = 60
var SHOWN_HOURS_TRESHOLD = 24

class NewMemberList extends Component {

  state = {
    new_members: [],
    lists: 0
  };

  getItems() {
    axios
    .get(API_GET_NEW_MEMBERS_URL+"/" + SHOWN_HOURS_TRESHOLD)
    .then( response =>  {
        const newState = {new_members: response.data};
        this.setState(newState);
    })
    .catch(error => console.log(error));

    axios
    .get(API_GET_LISTS_URL)
    .then (response => {
      const newState = {lists: response.data};
      this.setState(newState)
    })
  }

  componentDidMount() {
    this.timer = setInterval(() => this.getItems(), NOTIFICATION_TRESHOLD_MINUTES * 60 * 1000);
    this.getItems();
  }

  componentWillUnmount() {
    this.timer = null;
  }

  defaultPage() {
    const timeToDeadline = distanceInWords(new Date(), new Date(2019, 3, 0, 11), {locale: nblocale})
    return (
      <div className="newLists">
    <h1>{this.state.lists} lister på plass</h1>
    <h2>{timeToDeadline} til fristen!</h2>
      <div className="NewMemberList"><h1>STÅ PÅ, MILJØHELTER!</h1>
        <img alt="Arild på sykkel" src={arildBilde} />
      </div></div>);
  }

  createListItemForMember(member, i) {
    const signedUpTime = new Date(member.timestamp);

    const timeSinceWords = "for "+distanceInWordsToNow(signedUpTime, {locale: nblocale}) + " siden";
    const minutesSince = differenceInMinutes(new Date(), signedUpTime, {locale: nblocale});

  
    
    const myRef = React.createRef();

    return <li key={i} className={minutesSince < HILIGHT_TRESHOLD_MINUTES ? "new" : undefined}>
              <div className={"chapter"}>{member.chapter} </div>
              <div className="time"> {timeSinceWords}</div>
              {minutesSince < NOTIFICATION_TRESHOLD_MINUTES && 
                <audio ref={myRef} src={bikebell} autoPlay/>}
            </li>
  }

  render() {

    if (this.state.new_members.length < 2) {
      
      return this.defaultPage();
    }
    const timeToDeadline = distanceInWords(new Date(), new Date(2019, 3, 1, 12), {locale: nblocale})

    return (
    <div className="newLists">
    <h1>{this.state.lists} lister på plass</h1>
    <h2>{timeToDeadline} til fristen!</h2>
    
    <div className="NewMemberList">
      <h1>{this.state.new_members.length} NYE MEDLEMMER SISTE {SHOWN_HOURS_TRESHOLD} TIMER!</h1>

      <h2>Gratulerer med nytt medlem til:</h2>

      <ul>
        {this.state.new_members.map(this.createListItemForMember)}
      </ul>
    </div>
    </div>
    
    );
  }
}


export default NewMemberList;