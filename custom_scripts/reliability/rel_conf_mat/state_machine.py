from utils.enum import Enum
import re

class StateMachine():
    STATES = Enum('INITIAL SINGLE NUMBERED_MULTI UNNUMBERED_MULTI ERROR'.split())
    
    def __init__(self):
        self._reset_data_structs()

    def _reset_data_structs(self):
        self.single = []
        self.numbered_multi = []
        self.unnumbered_multi = []

        self.state = StateMachine.STATES.INITIAL
        self._container = None

    def divide_segs(self, segs, use_lena_segmentation=False):
        single = []
        numbered_multi = []
        unnumbered_multi = []
        for i in range(len(segs)):

            if use_lena_segmentation:
                segs[i].utters = self._combine_dot_split_utters(segs[i].utters)

            for j in range(len(segs[i].utters)):
                self._drive(segs[i].utters[j])
            self.finish()

            if self.state == StateMachine.STATES.ERROR:
                print 'The state machine has reached the error state. You should look into that.'

            single.extend(self.single)
            numbered_multi.extend(self.numbered_multi)
            unnumbered_multi.extend(self.unnumbered_multi)

            self._reset_data_structs()

        return single, numbered_multi, unnumbered_multi

    def _combine_dot_split_utters(self, utters):
        combined = []

        i = 0
        while i < len(utters):
            j = i + 1
            source = utters[i]
            while (j < len(utters) and
                   utters[j].is_dot_split and source.is_dot_split and
                   utters[j].start == source.start and
                   utters[j].end == source.end
            ):
                if utters[j].trans_phrase:
                    if source.trans_phrase is None:
                        source.trans_phrase = ''
                    source.trans_phrase += ' ' + utters[j].trans_phrase
                j += 1

            #source.is_dot_split = False
            combined.append(source)
            i = j

        return combined

    def _drive(self, utter):
        if self.state != StateMachine.STATES.ERROR:
            {
                StateMachine.STATES.INITIAL: self._state_initial,
                StateMachine.STATES.SINGLE: self._state_single,
                StateMachine.STATES.NUMBERED_MULTI: self._state_numbered_multi,
                StateMachine.STATES.UNNUMBERED_MULTI: self._state_unnumbered_multi,
                }[self.state](utter)

    def _state_initial(self, utter):
        if utter.is_dot_split:# and False:
            self.single.append([utter])
            
        elif not utter.is_dot_split:# or True:
            self._container = [utter]
            self.state = StateMachine.STATES.SINGLE

        # else:
        #     self.state = StateMachine.STATES.ERROR

    def _state_single(self, utter):
        if utter.is_dot_split:# and False:
            self.single.append(self._container)
            self.single.append([utter])
            self._container = None
            self.state = StateMachine.STATES.INITIAL
            
        elif (utter.start == self._container[0].start and
            utter.end == self._container[0].end):
            self._container.append(utter)
            if utter.speaker:
                self.state = StateMachine.STATES.NUMBERED_MULTI
            else:
                self.state = StateMachine.STATES.UNNUMBERED_MULTI

        elif (utter.start != self._container[0].start or
              utter.end != self._container[0].end):
            self.single.append(self._container)
            self._container = [utter]

        else:
            self.state = StateMachine.STATES.ERROR

    def _state_numbered_multi(self, utter):
        if (utter.start == self._container[-1].start and
            utter.end == self._container[-1].end):
            if utter.is_dot_split:# and False:
                self.state = StateMachine.STATES.ERROR
            else:
                self._container.append(utter)

        elif (utter.start != self._container[-1].start or
            utter.end != self._container[-1].end):
            if utter.is_dot_split:# and False:
                self.numbered_multi.append(self._container)
                self.single.append([utter])
                self._container = None
                self.state = StateMachine.STATES.INITIAL
            else:
                self.numbered_multi.append(self._container)
                self._container = [utter]
                self.state = StateMachine.STATES.SINGLE

        else:
            self.state = StateMachine.STATES.ERROR

    def _state_unnumbered_multi(self, utter):
        if (utter.start == self._container[-1].start and
            utter.end == self._container[-1].end):
            self._container.append(utter)
            if utter.speaker:
                self.state = StateMachine.STATES.NUMBERED_MULTI

        elif (utter.start != self._container[-1].start or
            utter.end != self._container[-1].end):
            if utter.is_dot_split:# and False:
                self.unnumbered_multi.append(self._container)
                self.single.append([utter])
                self._container = None
                self.state = StateMachine.STATES.INITIAL
            else:
                self.unnumbered_multi.append(self._container)
                self._container = [utter]
                self.state = StateMachine.STATES.SINGLE

        else:
            self.state = StateMachine.STATES.ERROR

    def finish(self):
        if self.state == StateMachine.STATES.SINGLE:
            self.single.append(self._container)
        elif self.state == StateMachine.STATES.NUMBERED_MULTI:
            self.numbered_multi.append(self._container)
        elif self.state == StateMachine.STATES.UNNUMBERED_MULTI:
            self.unnumbered_multi.append(self._container)

    def _print_container(self, array):
        array_name = '?'
        if array == self.single:
            array_name = 'single'
        elif array == self.numbered_multi:
            array_name = 'numbered_multi'
        elif array == self.unnumbered_multi:
            array_name = 'unnumbered_multi'
        
        container = array[-1]
        container_str = '%s - [' % (array_name)
        for i in range(len(container)):
            speaker = container[i].speaker.speaker_codeinfo.code if container[i].speaker else 'None'
            time_range = '%s-%s' % ( get_time_str(container[i].start), get_time_str(container[i].end) )
            trans_phrase = container[i].trans_phrase if container[i].trans_phrase else 'None'
            container_str += '%s:%s;%s' % (speaker, time_range, trans_phrase)
            if i < len(container) - 1:
                container_str += ', '
        container_str += ']'

        print container_str
