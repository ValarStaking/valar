
STATE_DEVIATION = -1
ALL_STATES_MATCH = 0
STATES_PENDING = 1


class DelcoChecker(object):

    def __init__(
        self, 
        # client,
        states,
    ):
        """Initialize checker.

        Parameters
        ----------
        client : object
            Validator ad or delegator contract client.
        targeted_states : list
            States that should be observed in the given sequence.
        """
        # self.prev_state = None
        self.targeted_states = states
        self.visited_states = []
        # self.client = client
        # self.client = None
        # Log initial state
        # self.update_state_log_if_state_changed()

    def update_state_history(self, state):
        """Checks previous state against current state and adds it to the history if there was a change.
        """
        # If first state or if different from previous state
        if len(self.visited_states) == 0 or state != self.visited_states[-1]:
            self.visited_states.append(state)
        # state = self.client.get_global_state().state.as_bytes
        # if state != self.prev_state:
        #     self.visited_states.append(state)
        #     self.prev_state = state

    # def have_target_states_been_visited(self):
    #     """Checks whether the target states have been visited.

    #     Returns
    #     -------
    #     bool
    #     """
    #     if len(self.targeted_states) != len(self.visited_states):
    #         return False
    #     for targeted_state, visited_state in zip(self.targeted_states, self.visited_states):
    #         if not targeted_state == visited_state:
    #             return False
    #     return True

    def check_completion(self) -> int:
        """Check whether states have been visited.

        Returns
        -------
        int
            Status flag (-1: bad, 0: done, 1: pending).
        """
        for targeted_state, visited_state in zip(self.targeted_states, self.visited_states):
            if not targeted_state == visited_state:
                return STATE_DEVIATION
        if len(self.targeted_states) == len(self.visited_states):
            return ALL_STATES_MATCH
        else:
            return STATES_PENDING
        