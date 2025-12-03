import React, { Component } from 'react';
import './NewMemberList.css';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';
import { differenceInMinutes } from 'date-fns';
import { nb as nblocale } from 'date-fns/locale';
import bikebell from './bikebell.mp3';
import arildBilde from './arild.jpeg';

// Use PUBLIC_URL for GitHub Pages subdirectory, fallback to empty for local dev
var API_GET_NEW_MEMBERS_URL = (process.env.PUBLIC_URL || '') + "/newmembers.json"
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
    .get(API_GET_NEW_MEMBERS_URL)
    .then( response =>  {
        // Filter by hour threshold on client side
        const now = new Date();
        const filtered = response.data.filter(member => {
          const memberTime = new Date(parseInt(member.timestamp));
          const hoursDiff = (now - memberTime) / (1000 * 60 * 60);
          return hoursDiff <= SHOWN_HOURS_TRESHOLD;
        });
        const newState = {new_members: filtered, response: true};
        this.setState(newState);
    })
    .catch(error => {
      console.log(error);
      // If file doesn't exist yet, set empty state
      this.setState({new_members: [], response: true});
    });
  }

  componentDidMount() {
    this.timer = setInterval(() => this.getItems(), NOTIFICATION_TRESHOLD_MINUTES * 60 * 1000);
    this.getItems();
  }

  componentWillUnmount() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
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

    const timeSinceWords = "for "+formatDistanceToNow(signedUpTime, {locale: nblocale}) + " siden";
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
        <div className="textLarge new">nye medlemmer</div>
        <div className="text">siste {SHOWN_HOURS_TRESHOLD} timer</div>
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