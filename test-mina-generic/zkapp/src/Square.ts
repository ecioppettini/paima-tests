import { Field, SmartContract, state, State, method, Reducer } from 'o1js';

export class Square extends SmartContract {
  @state(Field) num = State<Field>();

  reducer = Reducer({ actionType: Field });

  init() {
    super.init();
    this.num.set(Field(3));
  }

  events = {
    event1: Field,
    event2: Field,
  };

  @method async update(square: Field) {
    const currentState = this.num.get();
    this.num.requireEquals(currentState);
    square.assertEquals(currentState.mul(currentState));
    this.num.set(square);
    this.emitEvent('event1', square);
    this.emitEvent('event2', square.add(2));

    this.reducer.dispatch(square.add(3));
  }
}
