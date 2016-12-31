
import os
import datetime
import urllib

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CACHE_SERVER_BUFFER_MIN = 20
# discontinued 'http://weather.noaa.gov/pub/SL.us008001/ST.opnl/DF.gr2/'
NDFD_REMOTE_SERVER = 'http://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/'
NDFD_FILE_TEMPLATE = 'DC.ndfd/AR.{0}/VP.{1}/ds.{2}.bin'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NDFDFactoryMethods:
    """ Methods for downloading data from NDFD and generating directory
    and file paths.

    WARNING: Requires functionality contained in the base Seasonal Project
             Factory. So it MUST be included in a subclass based on the
             Seasonal Project Factory.
    """

    def initNDFD(self, server_url=NDFD_REMOTE_SERVER):
        self.setServerUrl(server_url)
        self.file_template = NDFD_FILE_TEMPLATE
        self.ndfd_config = self.sourceConfig('ndfd')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setServerUrl(self, server_url):
        self.server_url = server_url


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeOfLatestForecast(self):
        latest_time = datetime.datetime.utcnow()
        if latest_time.minute <= CACHE_SERVER_BUFFER_MIN:
            latest_time = (latest_time - datetime.timedelta(hours=1))
        return latest_time.replace(minute=0, second=0, microsecond=0)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def downloadLatestForecast(self, verbose=False):
        target_date = self.timeOfLatestForecast()
        filepaths = [ ]
        for temp_var in ('maxt','mint'):
            for time_span in ('001-003','004-007'):
                remote_uri = \
                    NDFD_FILE_TEMPLATE.format('conus', time_span, temp_var)
                if verbose:
                    print '\ndownloading :', remote_uri
                local_filepath = self.forecastGribFilepath(self.ndfd_config,
                                      target_date, time_span, temp_var)
                if verbose:
                    print 'to :', local_filepath
            
                url = self.server_url + remote_uri
                if verbose:
                    print 'url :', url
                urllib.urlretrieve(url, local_filepath)
                filepaths.append(local_filepath)

        return target_date, tuple(filepaths)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # forecast directory & data file path
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def forecastDownloadDir(self, fcast_date):
        # determine root directory of forecast tree
        if self.project.shared_forecast:
            fcast_dir = os.path.join(self.sharedRootDir(), 'forecast')
        else:
            fcast_dir = self.config.dirpaths.get('forecast', default=None)
            if fcast_dir is None:
                fcast_dir = os.path.join(self.projectRootDir(), 'forecast')
        # add subdirectory for forecast source
        download_dir = \
            os.path.join(fcast_dir, self.sourceToDirpath(self.ndfd_config))
        # add subdirectory for forecast date
        download_dir = \
            os.path.join(download_dir, self.timeToDirpath(fcast_date))
        # make sure directory exists before return
        if not os.path.exists(download_dir): os.makedirs(download_dir)
        return download_dir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def forecastGribFilename(self, fcast_date, time_span,
                                   variable, **kwargs):
        template = self.getDownloadFileTemplate(self.ndfd_config)
        template_args = dict(kwargs)
        template_args['date'] = self.timeToDirpath(fcast_date)
        template_args['source'] = self.sourceToFilepath(self.ndfd_config)
        template_args['timespan'] = time_span
        template_args['variable'] = variable
        return template % template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def forecastGribFilepath(self, ndfd_config, fcast_date, time_span,
                                   variable, **kwargs):
        fcast_dir = self.forecastDownloadDir(fcast_date)
        filename = \
           self.forecastGribFilename(fcast_date, time_span, variable, **kwargs)
        return os.path.join(fcast_dir, filename)

