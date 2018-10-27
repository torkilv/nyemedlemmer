import React from 'react';
import ReactDOM from 'react-dom';
import NewMemberList from './NewMemberList';

it('renders without crashing', () => {
  const div = document.createElement('div');
  ReactDOM.render(<NewMemberList />, div);
  ReactDOM.unmountComponentAtNode(div);
});
