import {initialIntent,Intent,nextSaturday} from './types';

export function exampleGroup():Intent {
  return {...initialIntent,date:nextSaturday(),party_size:4,max_stops:1,
    seeds:[{name:'Japanese Breakfast',category:'artist'}],interests:[],
    companions:[
      {label:'Alex',seeds:[{name:'Radiohead',category:'artist'}],interests:[],dietary:'none',accessible:false,budget:null},
      {label:'Sam',seeds:[{name:'Khruangbin',category:'artist'}],interests:[],dietary:'none',accessible:false,budget:null},
      {label:'Jordan',seeds:[{name:'Past Lives',category:'movie'}],interests:[],dietary:'none',accessible:false,budget:null},
    ]};
}
