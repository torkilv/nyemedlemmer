import React, { Component } from 'react';
import './NewMemberList.css';
import {Chart} from 'react-google-charts';
import axios from 'axios';
import distanceInWordsToNow  from 'date-fns/distance_in_words_to_now';
import nblocale from 'date-fns/locale/nb';
import arildBilde from './arild.jpeg';

var API_GET_DOORS_URL = "http://amiculous.com:5000/doors";
var NOTIFICATION_TRESHOLD_MINUTES = 3;

class NewMemberList extends Component {
  state = {
    new_members: [],
    lists: 0,
      doors: [[]],
      doors_extended : [[]]
  };

  getItems() {
    axios
      .get(API_GET_DOORS_URL)
      .then(response => {
        const newState = { doors: response.data };
        this.setState(newState);
      })
      .catch(error => console.log(error));
    axios
      .get(API_GET_DOORS_URL+"/extended")
      .then(response => {
        const newState = { doors_extended: response.data };
        this.setState(newState);
      })
      .catch(error => console.log(error));
  }

  componentDidMount() {
    this.timer = setInterval(
      () => this.getItems(),
      NOTIFICATION_TRESHOLD_MINUTES * 60 * 1000
    );
    this.getItems();
  }

  componentWillUnmount() {
    this.timer = null;
  }

  defaultPage() {
    return (
  
      <div className="NewMemberList"><h2>STÅ PÅ, MILJØHELTER!</h2>
        <img alt="Arild på sykkel" src={arildBilde} />
      </div>
    );
  }

  createDoorStat(doorStat) {
    const description = doorStat[0];
    const value = doorStat[1];
    return (<tr><th>{description}</th><td>{value}</td></tr>);
  }

  createDoorStats() {
    return (
      <div className="doorStats">
        <table><tbody>{this.state.doors.map(this.createDoorStat)}</tbody></table>
      </div>
    );
  }

  render() {
    let graphItem;
    graphItem = this.defaultPage();
    var doorStats = this.createDoorStats();
    const electionDay = new Date(2019, 8,9, 20 );
    const timeToElection = distanceInWordsToNow(electionDay, {locale: nblocale});
    return (
    <div className="app">
    <h1 className="headerNumbers">
      <div className="numberBox">
        {doorStats}
        <div className="text">{timeToElection} igjen til valget!</div>
      </div>
    </h1>
      {graphItem}
    </div>
    );
  }
}


export default NewMemberList;
