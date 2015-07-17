## @package parsers.parser_tools

import random

## This class encapsulates some common static methods used by various parsers.
class ParserTools(object):
    ## Checks whether or not a given segment passes all filters in a given list. The filters are run in such a way that any changes they make on the segment or it's utterances are made permanent.
    #  @param seg (Segment) the segment to put through the filters
    #  @param seg_filters (list) list of SegFilter objects
    #  @returns (boolean) True if segment passed all filters, False otherwise
    @staticmethod
    def include_seg(seg, seg_filters):
        i = 0
        included = True
        while i < len(seg_filters) and included:
            #make filter exclusions/changes permanent
            filtered_seg = seg_filters[i].filter_seg(seg)
            included = filtered_seg != None
            if included:
                seg.utters = filtered_seg.utters
            i += 1

        return included

    ## Picks n random segments from a list (without duplicates).
    #  @param n (int) number of segments to pick from the given list
    #  @param segs (list) List of Segment objects to pick from
    #  @returns (list) List of picked Segment objects. If returned list is empty, there were less than n segments in segs.
    @staticmethod
    def pick_rand_segs(n, segs):
        total_segs = len(segs)
        rand_indices = range(total_segs)
        random.shuffle(rand_indices)
        picked_segs = []

        if total_segs >= n:
            random.shuffle(rand_indices)
            picked_segs = map(lambda i: segs[i], rand_indices[:n])

        return picked_segs

    ## Picks n consecutive elements from a list.
    #  @param n (int) number of segments to pick from the given list
    #  @param segs (list) List of Segment objects to draw from
    #  @returns (list) List of n consecutive Segment objects. If returned list is empty, there were less than n segments in segs.
    @staticmethod
    def pick_contiguous_segs(n, segs):
        picked_segs = []

        if len(segs) >= n:
            picked_segs = segs[:n]

        return picked_segs
    
    @staticmethod
    def hacked_pick_rand_segs(n, segs, filename):
        taken_dict = None
        if filename == 'C003_20090708.csv':
            taken_dict = {
                #FAN
                '17242.17': True,
                '3964.05': True,
                '4657.84': True,
                '5050.81': True,
                '5443.52': True,
                '9028.79': True,
                '16972.12': True,
                '3725.36': True,
                '3838.99': True,
                '9077.36': True,
                '5559.10': True,
                '4846.05': True,
                '4624.57': True,
                '17524.45': True,
                '8713.28': True,
                '10557.96': True,
                '5081.40': True,
                '17250.11': True,
                '3686.86': True,
                '4211.19': True,
                '4546.91': True,
                '4016.98': True,
                '4483.29': True,
                '9026.90': True,
                '16385.44': True,
                '4483.92': True,
                '4588.89': True,
                '4992.00': True,
                '8875.75': True,
                '4568.56': True,
                '5033.57': True,
                '3719.53': True,
                '9365.84': True,
                #CHN                
                '4520.66': True,
                '17226.81': True,
                '5513.61': True,
                '4306.33': True,
                '5404.28': True,
                '4366.81': True,
                '3730.20': True,
                '16615.44': True,
                '3891.41': True,
                '7802.87': True,
                '8691.22': True,
                '10642.64': True,
                '7812.48': True,
                '9884.79': True,
                '16555.55': True,
                '8827.25': True,
                '9700.96': True,
                '3979.40': True,
                '16520.45': True,
                '4605.32': True,
                '5558.33': True,
                '10102.12': True,
                '9506.63': True,
                '8736.20': True,
                '17002.30': True,
                '17366.97': True,
                }
        
        elif filename == 'C006_20090827.csv':
            taken_dict = {
                #FAN
                '762.46': True,
                '12067.15': True,
                '2497.60': True,
                '2500.56': True,
                '4005.93': True,
                '7014.08': True,
                '1605.25': True,
                '758.74': True,
                '4980.74': True,
                '9862.81': True,
                '6114.66': True,
                '4016.32': True,
                '1678.45': True,
                '9750.89': True,
                '492.12': True,
                '10341.67': True,
                '4036.22': True,
                '3141.15': True,
                '8896.20': True,
                '5591.67': True,
                '3145.76': True,
                '9827.39': True,
                '7243.67': True,
                '3142.98': True,
                '11877.85': True,
                '372.73': True,
                '2711.66': True,
                '5754.33': True,
                '7824.91': True,
                '2297.99': True,
                '9510.07': True,
                '11902.29': True,
                '3129.17': True,
                '8699.76': True,
                #CHN
                '5265.42': True,
                '1613.54': True,
                '3705.76': True,
                '6663.56': True,
                '5065.69': True,
                '7011.00': True,
                '8115.81': True,
                '7865.42': True,
                '6878.60': True,
                '6315.12': True,
                '478.84': True,
                '4939.96': True,
                '2170.33': True,
                '6363.28': True,
                '10125.46': True,
                '1332.36': True,
                '10075.21': True,
                '10293.21': True,
                '1624.18': True,
                '2687.92': True,
                '996.51': True,
                '8781.95': True,
                '8822.81': True,
                '2596.32': True,
                '2667.29': True,
                '10089.00': True,
                '10021.41': True,
                '4376.08': True,
                '6348.46': True,
                '10107.56': True,
                '11251.48': True,
                '2499.73': True,
                '286.47': True,
                '8769.91': True,
                '4991.67': True,
                '2494.38': True,
                }
        
        elif filename == 'C023_20100823.csv':
            taken_dict = {
                    #FAN
                '21740.33': True,
                '2845.94': True,
                '17096.02': True,
                '33020.80': True,
                '31704.45': True,
                '20926.28': True,
                '17508.61': True,
                '17529.43': True,
                '32065.27': True,
                '14602.93': True,
                '771.12': True,
                '17830.76': True,
                '2328.79': True,
                '3512.89': True,
                '19930.19': True,
                '30807.89': True,
                '18001.32': True,
                '9981.22': True,
                '16902.46': True,
                '18589.66': True,
                '18372.09': True,
                '33937.65': True,
                '21280.72': True,
                '13412.66': True,
                '21867.95': True,
                '17899.45': True,
                '20739.55': True,
                '6468.05': True,
                '18492.06': True,
                '32959.28': True,
                '13252.51': True,
                '3779.60': True,
                '13298.03': True,
                '20507.62': True,
                '488.93': True,
                '13082.66': True,
                '22277.63': True,
                '16634.54': True,
                '18155.61': True,
                #CHN
                '11766.19': True,
                '434.36': True,
                '4178.19': True,
                '12018.17': True,
                '32117.80': True,
                '32780.66': True,
                '3202.78': True,
                '21645.76': True,
                '22653.66': True,
                '32936.19': True,
                '31512.64': True,
                '1562.17': True,
                '2538.92': True,
                '20384.04': True,
                '17322.38': True,
                '22500.27': True,
                '20650.86': True,
                '22929.71': True,
                '1418.28': True,
                '2353.34': True,
                '33608.65': True,
                '20330.16': True,
                '17939.05': True,
                '20193.14': True,
                '14497.25': True,
                '5211.13': True,
                '22274.30': True,
                '33747.42': True,
                '32619.74': True,
                '21627.21': True,
                '10561.03': True,
                '12331.10': True,
                '1160.63': True,
                '22190.38': True,
                }
            
        elif filename == 'C074_20130221.csv':
            taken_dict = {
                    #FAN
                '6705.6': True,
                '2984.55': True,
                '2855.29': True,
                '4023.14': True,
                '4734.26': True,
                '5638.11': True,
                '4437.63': True,
                '3022.48': True,
                '3633.28': True,

                #CHN
                '1125.92': True,
                '5354.19': True,
                '5010.58': True,
                '23.00': True,
                '4511.46': True,
                '4645.87': True,
                '4945.31': True,
                '156.59': True,
                '5170.13': True,
                '1373.89': True,
                '4600.50': True,
                '4573.14': True,
                '626.23': True,
                }
            
        elif filename == 'C085_20130311.csv':
            taken_dict = {
                #FAN
                '3982.13': True,
                '9272.77': True,
                '6761.11': True,
                '8251.69': True,
                '11734.68': True,
                '11199.65': True,
                '6409.41': True,
                '11804.76': True,
                '4833.22': True,
                '10393.21': True,
                '11736.97': True,
                '6016.37': True,
                '11467.62': True,
                '9108.90': True,
                '12071.67': True,
                '970.49': True,
                '11234.62': True,
                '11415.88': True,
                '5489.04': True,
                '6731.35': True,
                '7305.50': True,
                '7816.28': True,
                '4852.05': True,
                '5500.60': True,
                '5597.07': True,
                '5408.10': True,
                '6693.79': True,
                '6985.12': True,
                '6636.05': True,
                '7007.05': True,
                '11579.30': True,
                '8186.82': True,
                '7605.80': True,
                '7057.29': True,
                '9360.01': True,
                '2942.61': True,
                '4323.16': True,
                '11463.67': True,
                '9242.39': True,
                '5671.34': True,
                '578.54': True,
                '12035.77': True,
                
                #CHN
                '9824.82': True,
                '6833.14': True,
                '5266.27': True,
                '6015.64': True,
                '7262.01': True,
                '8063.05': True,
                '8424.66': True,
                '11348.86': True,
                '962.98': True,
                '8559.17': True,
                '7350.70': True,
                '8255.04': True,
                '7362.99': True,
                '13102.11': True,
                '636.92': True,
                '5199.32': True,
                '7342.88': True,
                '10080.56': True,
                '5413.87': True,
                '4063.53': True,
                '8333.67': True,
                '9865.08': True,
                '11256.24': True,
                '4540.65': True,
                '6381.08': True,
                '4899.32': True,
                '7507.60': True,
                '6465.93': True,
                '6942.53': True,
                '10046.31': True,
                '2973.70': True,
                '4534.57': True,
                '12091.98': True,
                '12017.46': True,
                '5204.61': True,
                '4926.44': True,
                '4505.40': True,
                '5920.17': True,
                '9114.44': True,
                }

        if taken_dict:
            hacked_segs = []
            for cur_seg in segs:
                start = '%0.2f' % (cur_seg.start)
                if start not in taken_dict:
                    hacked_segs.append(cur_seg)
            segs = hacked_segs
        
        total_segs = len(segs)
        rand_indices = range(total_segs)
        random.shuffle(rand_indices)
        picked_segs = []

        if total_segs >= n:
            random.shuffle(rand_indices)
            picked_segs = map(lambda i: segs[i], rand_indices[:n])

        return picked_segs
