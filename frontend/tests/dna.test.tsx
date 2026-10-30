import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import {afterEach,expect,it} from 'vitest';
import {TasteDNA} from '../components/TasteDNA';
afterEach(cleanup);
it('updates counts from actual inputs and explains its limits',()=>{
 const {rerender,container}=render(<TasteDNA seeds={[{name:'Radiohead',category:'artist'}]} interests={['art']}/>);
 expect(screen.getByText(/No inferred personality/)).toBeTruthy();
 expect(container.querySelector('.dna-bars b')?.textContent).toBe('1');
 rerender(<TasteDNA seeds={[]} interests={[]}/>);
 expect(container.querySelector('.dna-bars b')?.textContent).toBe('0');
});
