import React, { Component } from 'react';
import './NewMemberList.css';
import axios from 'axios';
import distanceInWordsToNow  from 'date-fns/distance_in_words_to_now';
import differenceInMinutes from 'date-fns/difference_in_minutes';
import nblocale from 'date-fns/locale/nb';
import bikebell from './bikebell.mp3';
import arildBilde from './arild.jpeg';

var API_GET_NEW_MEMBERS_URL = "http://pling.mdg.no:5000/newmembers"
var NOTIFICATION_TRESHOLD_MINUTES = 3
var HILIGHT_TRESHOLD_MINUTES = 60
var SHOWN_HOURS_TRESHOLD = 24

class NewMemberList extends Component {

  state = {
    new_members: [],
    response: false,
    lists: 0
  };

  getItems() {
    axios
    .get(API_GET_NEW_MEMBERS_URL+"/" + SHOWN_HOURS_TRESHOLD)
    .then( response =>  {
        const newState = {new_members: response.data, response: true};
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
        {this.state.response && <p>Ingen nye medlemmer funnet. Verv noen nye medlemmer her! http://mdg.no/bli-medlem</p>}
      </div>
    );
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

  createNewMembersList() {
    return (<div className="NewMemberList">

    <h1 className="headerNumbers"> 
      <div className="numberBox">
        <div className="number">{this.state.new_members.length}</div>
        <div className="textLarge">nye medlemmer</div>
        <div className="text">siste 24 timer</div>
      </div>
    </h1>

      <h2>Gratulerer med nytt medlem til:</h2>

      <ul>
        {this.state.new_members.map(this.createListItemForMember)}
      </ul>
    </div>)

  }

  render() {

    let newMembersItem;

    if (this.state.new_members.length < 1) {
      newMembersItem = this.defaultPage();
    } else {
      newMembersItem = this.createNewMembersList()
    }
    return (
    <div className="app">
    {newMembersItem}
    </div>
    
    );
  }
}


export default NewMemberList;