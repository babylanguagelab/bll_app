## @package parsers.stats_exporter

from utils.ui_utils import UIUtils
from parsers.trs_parser import TRSParser
from parsers.filter_manager import FilterManager

import csv

## This class writes statistics from the stats app to a csv file.
class StatsExporter(object):
    ## Constructor
    #  @param self
    #  @param config (Configuration) The output configuration to write to the csv file.
    def __init__(self, config, trs_filename, export_filename):
        self.config = config
        self.trs_filename = trs_filename
        self.export_filename = export_filename
        
        if not self.export_filename.lower().endswith('.csv'):
            self.export_filename += '.csv'

    ## Performs the write to the CSV file.
    #  @param self
    #  @param progress_update_fcn (function=None) function accepting a value in [0,1] to display as a progress bar - see utils.ProgressDialog. This value is used to indicate the level of completeness <em>of the current phase</em>
    #  @param progress_next_phase_fcn(function=None) - moves the progress bar to the next phase, which causes new text to be displayed in the bar - see utils.ProgressDialog
    def export(self, progress_update_fcn=None, progress_next_phase_fcn=None):
        #create csv file
        export_file = open(self.export_filename, 'wb')

        #write header info
        csv_writer = csv.writer(export_file, quoting=csv.QUOTE_ALL) #use Python csv library
        csv_writer.writerow(['Export Date: %s' % (UIUtils.get_cur_timestamp_str())])
        csv_writer.writerow(['Configuration Creation Date: %s' % (self.config.created)])
        csv_writer.writerow(['TRS Filename: %s' % (self.trs_filename)])
        csv_writer.writerow(['Output Configuration:'])
        csv_writer.writerow(['Name: %s' % (self.config.name)])
        csv_writer.writerow(['Description: %s' % (self.config.desc)])
        csv_writer.writerow([''])
        csv_writer.writerow(['Outputs:'])
        csv_writer.writerow([''])

        #parse the trs file
        trs_parser = TRSParser(self.trs_filename)
        segs = trs_parser.parse(progress_update_fcn, progress_next_phase_fcn, validate=False)
        chains = None #this is populated on demand, then cached

        #iterate through all outputs in the configuration, adding segments/chains to each one, then writing the output to the spreadsheet file
        i = 0
        while i < len(self.config.outputs):
            #update progress bar text
            if progress_next_phase_fcn:
                progress_next_phase_fcn()
                
            cur_output = self.config.outputs[i]
            cur_output.reset() #clear any cached utterances from previous runs

            #if we need chains, parse them from the segment list
            if cur_output.chained and not chains:
                chains = FilterManager.get_chains(segs)

            #add chains/segments to the current output
            items = chains if cur_output.chained else segs
            j = 0
            while j < len(items):
                cur_output.add_item(items[j], filter_utters=True) #note: filter_utters only affects segs (not chains)
                j += 1

            #note: updating progress individually within the above loop (for every iteration of j) slows down the processing considerably (by a factor of ~4) - a compromise is to just set each phase to 100% after it completes.
            if progress_update_fcn:
                progress_update_fcn(1)

            #grab the output's results and write them to the file
            cur_output.write_csv_rows(csv_writer)
            csv_writer.writerow([''])
            
            i += 1

        export_file.close()
