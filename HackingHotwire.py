

# Do imports
import os
import time
import copy
import numpy as np
import collections as cl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm


# Do local imports
from input_arguments import (
    report_name as             S_REPORT_NAME,
    hotel_filter as            D_HOTEL_FILTER,
    geographic_goto_address as S_GEOGRAPHIC_GOTO_ADDRESS,
    search_query_url as        S_SEARCH_QUERY_URL,
    hack_mode as               S_HACK_MODE,
    generate_report as         B_GENERATE_REPORT,
)
from additional_functions import generate_report_pdf


class HackingHotwire:


    def __init__(self, s_report_name='report.pdf', d_hotel_filter=None, s_geographic_goto_address=None):

        # Check that keys for hotel filters are valid
        if d_hotel_filter is not None:
            assert set(d_hotel_filter) <= set(['f_hotel_class', 'f_guest_rating', 'f_savings_pct', 'f_geographic_distance']), \
                '\nError:\td_hotel_filter can only contain keys in [\'f_hotel_class\', \'f_guest_rating\', \'f_savings_pct\']'
            if 'f_hotel_class' in d_hotel_filter:
                assert (d_hotel_filter['f_hotel_class'] >= 1) and (d_hotel_filter['f_hotel_class'] <= 5), \
                    '\nError:\tf_hotel_class filter value expected to be in [1, 5]'
            if 'f_guest_rating' in d_hotel_filter:
                assert (d_hotel_filter['f_guest_rating'] >= 1) and (d_hotel_filter['f_guest_rating'] <= 5), \
                    '\nError:\tf_guest_rating filter value expected to be in [1, 5]'
            if 'f_savings_pct' in d_hotel_filter:
                assert (d_hotel_filter['f_savings_pct'] >= 0.0) and (d_hotel_filter['f_savings_pct'] <= 100.0), \
                    '\nError:\tf_savings_pct filter value expected to be in [0.0, 100.0]'
            if 'f_geographic_distance' in d_hotel_filter:
                assert (d_hotel_filter['f_geographic_distance'] >= 0.0) and (s_geographic_goto_address is not None), \
                    '\nError:\tf_geographic_distance filter value expected to be in [0.0, inf), and s_geographic_goto_address must not be None'

        # Define instance variables
        self.s_report_name = s_report_name
        self.d_hotel_filter = d_hotel_filter if d_hotel_filter is None else cl.defaultdict(lambda: None, d_hotel_filter)
        self.s_geographic_goto_address = s_geographic_goto_address

        # Set webdriver parameters
        o_option = webdriver.ChromeOptions()
        o_option.binary_location = 'browser\Win_948375_chrome-win\chrome-win\chrome.exe'
        o_option.add_experimental_option('excludeSwitches', ['enable-automation'])
        o_option.add_experimental_option('useAutomationExtension', False)
        o_option.add_argument('--disable-blink-features=AutomationControlled')

        # Initialize driver
        self.o_driver = webdriver.Chrome(executable_path='browser\chromedriver_win32\chromedriver', options=o_option)
        self.o_driver.implicitly_wait(10)
        self.o_driver.maximize_window()

        # Define metadata template data structures
        self.d_hotel_comparison_attributes_template = {
            'f_hotel_class': None,
            's_distance': None,
            'f_guest_rating': None,
            'i_reviews_total': None,
            'ls_amenities': None,
            'i_list_price': None,
            's_condition_rating': None,
            's_service_rating': None,
            's_cleanliness_rating': None,
        }
        self.d_hotel_additional_attributes_template = {
            's_hotel_name': None,
            'i_sale_price': None,
            'f_final_price': None,
            'f_savings_pct': None,
            's_hotel_address': None,
            'f_geographic_distance': None,
            's_geographic_url': None,
        }


    def _open_page(self, s_url, s_error_page_text=None, i_wait_extra=None):

        # Open webpage and retry if error page loads
        while True:
            try:
                self.o_driver.get(s_url)
                if s_error_page_text is not None:
                    s_page_text = self.o_driver.find_element(By.TAG_NAME, 'body').text
                    if s_page_text == s_error_page_text:
                        continue
                    else:
                        break
                else:
                    break
            except:
                time.sleep(1)
                continue
        if i_wait_extra is not None:
            time.sleep(i_wait_extra)


    def load_all_hotels(self):

        # Load all hotels available
        while True:
            try:

                # Check if all hotels are showing
                s_showing_info = self.o_driver.find_element(By.CLASS_NAME, 'showing-results-count').text
                i_showing_nth = int(s_showing_info.split('- ')[1].split(' out')[0])
                i_showing_total = int(s_showing_info.split(' ')[-1])
                if i_showing_nth == i_showing_total:
                    break

                # Click to load next batck
                self.o_driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                self.o_driver.find_element(By.CLASS_NAME, 'show-more-results__button').click()
            except:
                time.sleep(1)
                continue
        self.o_driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')


    def get_hotel_metadata_primary(self):

        # Grab primary hotel metadata
        ld_hotel_metadata_hotrate = []
        ld_hotel_metadata_normal = []
        lo_hotel_cards = self.o_driver.find_elements(By.CLASS_NAME, 'result-list-components')
        o_tqdm = tqdm(lo_hotel_cards)
        o_tqdm.set_description('Fetching Primary Metadata')
        for o_hotel_card in o_tqdm:

            # Determine whether card is for a hotrate or normal hotel
            b_hotrate = '-star' in o_hotel_card.find_element(By.CLASS_NAME, 'HotelCardLayout__hotel-name').text

            # Determine hotel page url
            s_hotel_url = o_hotel_card.find_element(By.XPATH, ".//a[@target='_blank']").get_attribute('href')

            # Extract hotel comparison attributes
            try:
                i_star_segments_filled = len(o_hotel_card.find_elements(By.XPATH, ".//*[name()='svg']//*[@fill='url(#star-gradient)']"))
                i_star_segments_unfilled = len(o_hotel_card.find_elements(By.XPATH, ".//*[name()='svg']//*[@fill='#DEE1E7']"))
                f_hotel_class = float(i_star_segments_filled) if i_star_segments_filled + i_star_segments_unfilled == 5 else i_star_segments_filled - 0.5
            except:
                f_hotel_class = None
            try:
                s_distance = o_hotel_card.find_element(By.CLASS_NAME, 'HotelCardLayout__distance').text
            except:
                s_distance = None
            try:
                f_guest_rating = float(o_hotel_card.find_element(By.CLASS_NAME, 'RatingTag').text[:-2])
            except:
                f_guest_rating = None
            try:
                i_reviews_total = int(o_hotel_card.find_element(By.CLASS_NAME, 'Reviews').text.replace('(', '').replace(')', '').replace('reviews', ''))
            except:
                i_reviews_total = None
            try:
                ls_amenities = sorted([o_element.find_element(By.TAG_NAME, 'svg').get_attribute('data-id') 
                                       for o_element in o_hotel_card.find_elements(By.CLASS_NAME, 'AmenityIcon__icon')])
            except:
                ls_amenities = None
            try:
                if b_hotrate:
                    i_list_price = int(o_hotel_card.find_element(By.CLASS_NAME, 'price-blocks__strikethrough').get_attribute('textContent')[1:]) + 1
                else:
                    i_list_price = int(o_hotel_card.find_element(By.CLASS_NAME, 'price-blocks__price').get_attribute('textContent')[1:])
            except:
                i_list_price = None

            # Extract hotel additional attributes
            try:
                s_hotel_name = o_hotel_card.find_element(By.CLASS_NAME, 'HotelCardLayout__hotel-name').text
            except:
                s_hotel_name = None
            try:
                i_sale_price = int(o_hotel_card.find_element(By.CLASS_NAME, 'price-blocks__price').get_attribute('textContent')[1:])
            except:
                i_sale_price = None

            # Store hotel comparison attributes
            d_hotel_comparison_attributes = copy.copy(self.d_hotel_comparison_attributes_template)
            d_hotel_comparison_attributes.update({
                    'f_hotel_class': f_hotel_class,
                    's_distance': s_distance,
                    'f_guest_rating': f_guest_rating,
                    'i_reviews_total': i_reviews_total,
                    'ls_amenities': ls_amenities,
                    'i_list_price': i_list_price,
            })

            # Store hotel additional attributes
            d_hotel_additional_attributes = copy.copy(self.d_hotel_additional_attributes_template)
            d_hotel_additional_attributes.update({
                's_hotel_name': s_hotel_name,
                'i_sale_price': i_sale_price,
            })

            # Store hotel attributes
            d_hotel_metadata = {
                's_hotel_url': s_hotel_url,
                'd_hotel_comparison_attributes': d_hotel_comparison_attributes,
                'd_hotel_additional_attributes': d_hotel_additional_attributes,
            }
            if b_hotrate:
                ld_hotel_metadata_hotrate.append(d_hotel_metadata)
            else:
                ld_hotel_metadata_normal.append(d_hotel_metadata)

        # Return metadata for hotrate and normal hotels
        return ld_hotel_metadata_hotrate, ld_hotel_metadata_normal


    def get_hotel_metadata_secondary(self, ld_hotel_metadata_hotrate, ld_hotel_metadata_normal, na_attribute_matches):

        # Grab secondary hotel metadata
        o_tqdm = tqdm(range(na_attribute_matches.shape[0]))
        o_tqdm.set_description('Fetching Secondary Metadata')
        for i_row_idx in o_tqdm:

            # If hotel filter requirements are not met, skip
            if self.d_hotel_filter is not None:
                lb_filters_triggered = [ld_hotel_metadata_hotrate[i_row_idx]['d_hotel_comparison_attributes'][s_attribute] < self.d_hotel_filter[s_attribute] 
                                        for s_attribute in self.d_hotel_filter if s_attribute in ld_hotel_metadata_hotrate[i_row_idx]['d_hotel_comparison_attributes']]
                if any(lb_filters_triggered):
                    continue

            # Get hotrate hotel metadata
            d_hotel_metadata_hotrate = ld_hotel_metadata_hotrate[i_row_idx]

            # Get hotrate hotel page url
            s_hotel_url_hotrate = d_hotel_metadata_hotrate['s_hotel_url']

            # Open hotrate hotel webpage
            while True:
                self._open_page(s_hotel_url_hotrate, s_error_page_text='Not found')
                try:
                    WebDriverWait(self.o_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'hw-hotel-description__name-container')))
                    WebDriverWait(self.o_driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'GuestRatingProgressBar__counter')))
                    break
                except:
                    pass
                if len(self.o_driver.find_elements(By.CLASS_NAME, 'deals-gone-details-alert__title')) > 0:
                    continue

            # Load all hotrate hotel ratings
            b_page_load_alert = False
            while True:
                try:
                    lo_guest_ratings = self.o_driver.find_elements(By.CLASS_NAME, 'GuestRatingProgressBar__counter')
                    s_condition_rating = lo_guest_ratings[0].text
                    s_service_rating = lo_guest_ratings[1].text
                    s_cleanliness_rating = lo_guest_ratings[3].text
                    break
                except:

                    # Handle case where deal disappeared
                    i_deal_gone_alerts_num = len(self.o_driver.find_elements(By.CLASS_NAME, 'deals-gone-details-alert'))
                    if i_deal_gone_alerts_num > 0:
                        b_page_load_alert = True
                        break
                    time.sleep(1)
                    continue
            if b_page_load_alert:
                continue

            # Store hotrate hotel comparison attributes
            d_hotel_metadata_hotrate['d_hotel_comparison_attributes'].update({
                's_condition_rating': s_condition_rating,
                's_service_rating': s_service_rating,
                's_cleanliness_rating': s_cleanliness_rating,
            })

            # Iterate over normal hotels
            li_col_idxs = np.argwhere(na_attribute_matches[i_row_idx].sum(axis=1).astype(bool)).ravel()
            for i_col_ctr, i_col_idx in tqdm(enumerate(li_col_idxs)):

                # Update description
                o_tqdm.set_description(f'Fetching Secondary Metadata ({i_col_ctr + 1}/{len(li_col_idxs)})')

                # If hotel filter requirements are not met, skip
                if self.d_hotel_filter is not None:
                    lb_filters_triggered = [ld_hotel_metadata_normal[i_col_idx]['d_hotel_comparison_attributes'][s_attribute] < self.d_hotel_filter[s_attribute] 
                                            for s_attribute in self.d_hotel_filter if s_attribute in ld_hotel_metadata_normal[i_col_idx]['d_hotel_comparison_attributes']]
                    if any(lb_filters_triggered):
                        continue

                # Get normal hotel metadata
                d_hotel_metadata_normal = ld_hotel_metadata_normal[i_col_idx]

                # Continue normal hotel attributes already fetched
                if ((d_hotel_metadata_normal['d_hotel_comparison_attributes']['s_condition_rating'] is not None) and 
                    (d_hotel_metadata_normal['d_hotel_comparison_attributes']['s_service_rating'] is not None) and 
                    (d_hotel_metadata_normal['d_hotel_comparison_attributes']['s_cleanliness_rating'] is not None)):
                    continue

                # Get normal hotel page url
                s_hotel_url_normal = d_hotel_metadata_normal['s_hotel_url']

                # Open normal hotel webpage
                self._open_page(s_hotel_url_normal, s_error_page_text='Not found')

                # Load all normal hotel ratings
                while True:
                    try:
                        self.o_driver.find_element(By.XPATH, ".//button[@data-stid='reviews-link']").click()
                        WebDriverWait(self.o_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'uitk-progress-bar-value')))
                        break
                    except:
                        time.sleep(1)
                        continue
                while True:
                    try:
                        lo_guest_ratings = self.o_driver.find_elements(By.CLASS_NAME, 'uitk-progress-bar-value')
                        s_condition_rating = lo_guest_ratings[3].text[:-2]
                        s_service_rating = lo_guest_ratings[1].text[:-2]
                        s_cleanliness_rating = lo_guest_ratings[0].text[:-2]
                        break
                    except:
                        time.sleep(1)
                        continue 

                # Store normal hotel attributes
                d_hotel_metadata_normal['d_hotel_comparison_attributes'].update({
                    's_condition_rating': s_condition_rating,
                    's_service_rating': s_service_rating,
                    's_cleanliness_rating': s_cleanliness_rating,
                })

        # Return metadata for hotrate and normal hotels
        return ld_hotel_metadata_hotrate, ld_hotel_metadata_normal


    def get_attribute_matches(self, ld_hotel_metadata_hotrate, ld_hotel_metadata_normal):

        # Find attribute matches
        na_attribute_matches = np.zeros((len(ld_hotel_metadata_hotrate), len(ld_hotel_metadata_normal), len(self.d_hotel_comparison_attributes_template)))
        for i_row_idx, d_hotel_metadata_hotrate in enumerate(ld_hotel_metadata_hotrate):
            for i_col_idx, d_hotel_metadata_normal in enumerate(ld_hotel_metadata_normal):
                for i_dep_idx, s_attribute in enumerate(self.d_hotel_comparison_attributes_template):
                    if ((d_hotel_metadata_hotrate['d_hotel_comparison_attributes'][s_attribute] is None) or 
                        (d_hotel_metadata_normal['d_hotel_comparison_attributes'][s_attribute] is None)):
                        continue
                    elif d_hotel_metadata_hotrate['d_hotel_comparison_attributes'][s_attribute] == d_hotel_metadata_normal['d_hotel_comparison_attributes'][s_attribute]:
                            na_attribute_matches[i_row_idx, i_col_idx, i_dep_idx] = 1
                    elif d_hotel_metadata_hotrate['d_hotel_comparison_attributes'][s_attribute] != d_hotel_metadata_normal['d_hotel_comparison_attributes'][s_attribute]:
                            na_attribute_matches[i_row_idx, i_col_idx, :] = 0
                            break

        # Return match matrix
        return na_attribute_matches


    def parse_metadata_by_matches(self, ld_hotel_metadata_hotrate, ld_hotel_metadata_normal, na_attribute_matches):

        # Find perfect hotrate to normal hotel matches
        ld_hotel_metadata_decoded = []
        for i_row_idx in range(na_attribute_matches.shape[0]):

            # If there is not exactly one perfect normal hotel match, skip
            na_perfect_normal_hotel_match_idxs = np.where(na_attribute_matches[i_row_idx, :, :].sum(axis=1).astype(bool))[0].ravel()
            if len(na_perfect_normal_hotel_match_idxs) != 1:
                continue
            i_perfect_normal_hotel_match_idx = int(na_perfect_normal_hotel_match_idxs[0])

            # Define metadata data structures
            d_hotel_metadata_hotrate = ld_hotel_metadata_hotrate[i_row_idx]
            d_hotel_metadata_normal = ld_hotel_metadata_normal[i_perfect_normal_hotel_match_idx]
            d_attributes_matched = copy.copy(self.d_hotel_comparison_attributes_template)
            d_attributes_matched.update({list(self.d_hotel_comparison_attributes_template.keys())[i_attribute_idx]: 
                True for i_attribute_idx in np.argwhere(na_attribute_matches[i_row_idx, i_perfect_normal_hotel_match_idx]).ravel()})

            # Store decoded metadata
            ld_hotel_metadata_decoded.append({
                'd_hotel_metadata_hotrate': d_hotel_metadata_hotrate,
                'd_hotel_metadata_normal': d_hotel_metadata_normal,
                'd_attributes_matched': d_attributes_matched,
            })

        # Return decoded metadata
        return ld_hotel_metadata_decoded


    def get_hotel_metadata_misc(self, ld_hotel_metadata_decoded):

        # Collect miscellaneous hotel data for each decoded hotel
        o_tqdm = tqdm(ld_hotel_metadata_decoded)
        o_tqdm.set_description('Fetching Misc Metadata')
        for d_hotel_metadata_decoded in o_tqdm:

            # Get hotrate hotel page url
            s_hotel_url_hotrate = d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['s_hotel_url']

            # Open hotrate hotel webpage
            while True:
                self._open_page(s_hotel_url_hotrate, s_error_page_text='Not found')
                try:
                    WebDriverWait(self.o_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'hw-hotel-description__name-container')))
                    WebDriverWait(self.o_driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'details-bed-types__bed-choice__book-now')))
                    break
                except:
                    pass
                if len(self.o_driver.find_elements(By.CLASS_NAME, 'deals-gone-details-alert__title')) > 0:
                    continue

            # Get hotrate hotel final price
            while True:
                try:
                    self.o_driver.find_elements(By.CLASS_NAME, 'details-bed-types__bed-choice__book-now')[0].click()
                    WebDriverWait(self.o_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'review-policy-book__total-charge-amount')))
                    break
                except:
                    time.sleep(1)
                    continue
            while True:
                try:
                    f_final_price = float(self.o_driver.find_element(By.CLASS_NAME, 'review-policy-book__total-charge-amount').text[1:-4].replace(',', ''))
                    break
                except:
                    time.sleep(1)
                    continue

            # Store hotrate hotel additional attributes
            d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_additional_attributes'].update({
                'f_final_price': f_final_price,
            })

            # Get normal hotel page url
            s_hotel_url = d_hotel_metadata_decoded['d_hotel_metadata_normal']['s_hotel_url']

            # Open normal hotel webpage
            self._open_page(s_hotel_url, s_error_page_text='Not found')

            # Get normal hotel address
            try:
                s_hotel_address = self.o_driver.find_element(By.XPATH, ".//div[@data-stid='content-hotel-address']").text
            except:
                s_hotel_address = None

            # Store normal hotel additional attributes
            d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_additional_attributes'].update({
                's_hotel_address': s_hotel_address,
            })

        # Return decoded metadata
        return ld_hotel_metadata_decoded


    def get_geographic_metadata(self, ld_hotel_metadata_decoded):

        # Skip if necessary input data is not specified
        if self.s_geographic_goto_address is None:
            return

        # Find geographic metadata
        o_tqdm = tqdm(ld_hotel_metadata_decoded)
        o_tqdm.set_description('Fetching Geographic Data')
        for d_hotel_metadata_decoded in o_tqdm:

            # Get normal hotel address
            s_hotel_address = d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_additional_attributes']['s_hotel_address']

            # Address case when no address could be found
            # Store geographic attributes
            if s_hotel_address is None:
                d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_additional_attributes'].update({
                    'f_geographic_distance': None,
                    's_geographic_url': None,
                })
                continue

            # Open google maps
            self._open_page('https://www.google.com/maps/dir/')

            # Search for a route between two points
            while True:
                try:
                    self.o_driver.find_element(By.ID, 'directions-searchbox-0').find_element(By.CLASS_NAME, 'tactile-searchbox-input').send_keys(self.s_geographic_goto_address)
                    self.o_driver.find_element(By.ID, 'directions-searchbox-1').find_element(By.CLASS_NAME, 'tactile-searchbox-input').send_keys(s_hotel_address + '\n')
                    break
                except:
                    time.sleep(1)
                    continue
            while True:
                try:
                    self.o_driver.find_element(By.XPATH, ".//img[@aria-label='Driving']").click()
                    break
                except:
                    time.sleep(1)
                    continue
            while True:
                try:
                    f_geographic_distance = float(
                        self.o_driver.find_element(By.ID, 'section-directions-trip-0').find_element(By.CLASS_NAME, 'fontBodyMedium').text.split(' ')[0].replace(',', ''))
                    break
                except:
                    try:
                        if 'Google Maps can\'t find' in self.o_driver.find_element(By.CLASS_NAME, 'widget-directions').find_element(By.ID, 'sbsg51').text:
                            f_geographic_distance = None
                            break
                    except:
                        pass
                    time.sleep(1)
                    continue
            while True:
                s_geographic_url = self.o_driver.current_url
                if s_geographic_url == 'https://www.google.com/maps/dir/':
                    time.sleep(1)
                    continue
                else:
                    break
            
            # Store geographic attributes
            d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_additional_attributes'].update({
                'f_geographic_distance': f_geographic_distance,
                's_geographic_url': s_geographic_url,
            })

        # Return updated metadata
        return ld_hotel_metadata_decoded


    def parse_metadata_by_filters(self, ld_hotel_metadata_decoded):

        # Find hotels that match filter criteria
        ld_hotel_metadata_decoded_parsed = []
        for d_hotel_metadata_decoded in ld_hotel_metadata_decoded:

            # Extract relevant metadata data structure
            d_hotel_metadata_hotrate = d_hotel_metadata_decoded['d_hotel_metadata_hotrate']
            d_hotel_metadata_normal = d_hotel_metadata_decoded['d_hotel_metadata_normal']

            # Calculate savings
            # Store savings value
            f_savings_pct = round(100.0 * (1.0 - (d_hotel_metadata_hotrate['d_hotel_additional_attributes']['i_sale_price'] / 
                                  float(d_hotel_metadata_normal['d_hotel_comparison_attributes']['i_list_price']))), 2)
            d_hotel_metadata_hotrate['d_hotel_additional_attributes']['f_savings_pct'] = f_savings_pct

            # If hotel filter requirements are not met, skip
            if self.d_hotel_filter is not None:
                b_filter_hotel = False
                for s_attribute in self.d_hotel_filter:
                    if s_attribute == 'f_savings_pct':
                        if d_hotel_metadata_hotrate['d_hotel_additional_attributes']['f_savings_pct'] <= self.d_hotel_filter[s_attribute]:
                            b_filter_hotel = True
                    elif s_attribute == 'f_geographic_distance':
                        if d_hotel_metadata_normal['d_hotel_additional_attributes']['f_geographic_distance'] is None:
                            b_filter_hotel = True
                        elif d_hotel_metadata_normal['d_hotel_additional_attributes']['f_geographic_distance'] > self.d_hotel_filter[s_attribute]:
                            b_filter_hotel = True
                    else:
                        if d_hotel_metadata_hotrate['d_hotel_comparison_attributes'][s_attribute] is None:
                            b_filter_hotel = True
                        elif d_hotel_metadata_hotrate['d_hotel_comparison_attributes'][s_attribute] < self.d_hotel_filter[s_attribute]:
                            b_filter_hotel = True
                if b_filter_hotel:
                    continue

            # Update parsed list
            ld_hotel_metadata_decoded_parsed.append(d_hotel_metadata_decoded)

        # Return decoded metadata
        return ld_hotel_metadata_decoded_parsed


    def hack_hotwire_basic(self, s_search_query_url, b_for_advanced=False):

        # Open query page
        self._open_page(s_search_query_url, s_error_page_text='Not found', i_wait_extra=15)

        # Apply hotel filter requirements
        if self.d_hotel_filter is not None:
            if 'f_hotel_class' in self.d_hotel_filter:
                while True:
                    try:
                        self.o_driver.find_element(By.CLASS_NAME, 'star_rating_filter').click()
                        for i_hotel_class_checkbox_idx in range(int(np.floor(5 - self.d_hotel_filter['f_hotel_class'])) + 1):
                            o_hotel_class_element = self.o_driver.find_element(
                                By.CLASS_NAME, 'star_rating_filter').find_elements(By.CLASS_NAME, 'ListBuilderItem')[i_hotel_class_checkbox_idx]
                            if 'ListBuilderItem__disabled' in o_hotel_class_element.get_attribute('class'):
                                continue
                            o_hotel_class_element.find_element(By.CLASS_NAME, 'filter-text').click()
                        self.o_driver.find_element(By.CLASS_NAME, 'star_rating_filter').click()
                        break
                    except:
                        time.sleep(1)
                        continue
            if 'f_guest_rating' in self.d_hotel_filter:
                if self.d_hotel_filter['f_guest_rating'] >= 3.5:
                    self.o_driver.find_element(By.CLASS_NAME, 'guest_rating_filter').click()
                    while True:
                        try:
                            self.o_driver.find_element(By.CLASS_NAME, 'guest_rating_filter').click()
                            i_guest_rating_radiobutton_idx = min(int(np.ceil((5 - self.d_hotel_filter['f_guest_rating']) / 0.5)), 4)
                            self.o_driver.find_element(By.CLASS_NAME, 'guest_rating_filter').find_elements(By.CLASS_NAME, 'label-text')[i_guest_rating_radiobutton_idx].click()
                            break
                        except:
                            time.sleep(1)
                            continue

        # Load all hotels
        self.load_all_hotels()

        # Get primary hotel metadata
        ld_hotel_metadata_hotrate, ld_hotel_metadata_normal = self.get_hotel_metadata_primary()

        # Determine attribute matches
        na_attribute_matches = self.get_attribute_matches(ld_hotel_metadata_hotrate, ld_hotel_metadata_normal)

        # Parse and get geographic metadata for basic search
        ld_hotel_metadata_decoded = None
        if not b_for_advanced:

            # Parse to keep only relevant data by matches
            ld_hotel_metadata_decoded = self.parse_metadata_by_matches(ld_hotel_metadata_hotrate, ld_hotel_metadata_normal, na_attribute_matches)

            # Get miscellaneous other metadata
            ld_hotel_metadata_decoded = self.get_hotel_metadata_misc(ld_hotel_metadata_decoded)

            # Get geographic metadata
            ld_hotel_metadata_decoded = self.get_geographic_metadata(ld_hotel_metadata_decoded)

            # Parse to keep only relevant data by filters
            ld_hotel_metadata_decoded = self.parse_metadata_by_filters(ld_hotel_metadata_decoded)

            # Drop secondary metadata comparison attributes
            for d_hotel_metadata_decoded in ld_hotel_metadata_decoded:
                del d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_comparison_attributes']['s_condition_rating']
                del d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_comparison_attributes']['s_service_rating']
                del d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_comparison_attributes']['s_cleanliness_rating']

        # Define data structure of granular metadata
        d_hotel_metadata_granular = {
            'ld_hotel_metadata_hotrate': ld_hotel_metadata_hotrate, 
            'ld_hotel_metadata_normal': ld_hotel_metadata_normal, 
            'na_attribute_matches': na_attribute_matches
        }

        # Return hotel metadata and attribute matches
        return ld_hotel_metadata_decoded, d_hotel_metadata_granular


    def hack_hotwire_advanced(self, s_search_query_url):

        # Get attribute matches based on primary hotel metadata
        _, d_hotel_metadata_granular = self.hack_hotwire_basic(s_search_query_url, b_for_advanced=True)

        # Add in secondary hotel metadata
        ld_hotel_metadata_hotrate, ld_hotel_metadata_normal = self.get_hotel_metadata_secondary(**d_hotel_metadata_granular)

        # Determine attribute matches
        na_attribute_matches = self.get_attribute_matches(ld_hotel_metadata_hotrate, ld_hotel_metadata_normal)

        # Parse to keep only relevant data by matches
        ld_hotel_metadata_decoded = self.parse_metadata_by_matches(ld_hotel_metadata_hotrate, ld_hotel_metadata_normal, na_attribute_matches)

        # Get miscellaneous other metadata
        ld_hotel_metadata_decoded = self.get_hotel_metadata_misc(ld_hotel_metadata_decoded)

        # Get geographic metadata
        ld_hotel_metadata_decoded = self.get_geographic_metadata(ld_hotel_metadata_decoded)

        # Parse to keep only relevant data by filters
        ld_hotel_metadata_decoded = self.parse_metadata_by_filters(ld_hotel_metadata_decoded)

        # Return hotel metadata and attribute matches
        return ld_hotel_metadata_decoded


    def hack_hotwire(self, s_search_query_url, s_hack_mode='basic', b_generate_report=False):

        # Check that arguments are valid
        assert s_hack_mode in ['basic', 'advanced'], \
            '\nError:\ts_hack_mode expected to be in [\'basic\', \'advanced\']'

        # Get hotel metadata and attribute matches
        if s_hack_mode == 'basic':
            ld_hotel_metadata_decoded, _ = self.hack_hotwire_basic(s_search_query_url)
        elif s_hack_mode == 'advanced':
            ld_hotel_metadata_decoded = self.hack_hotwire_advanced(s_search_query_url)
        self.o_driver.close()

        # Sort hotels
        d_filter_to_get_value = {
            'f_hotel_class': lambda d: -d['d_hotel_metadata_normal']['d_hotel_comparison_attributes']['f_hotel_class'],
            'f_guest_rating': lambda d: -d['d_hotel_metadata_normal']['d_hotel_comparison_attributes']['f_guest_rating'],
            'f_savings_pct': lambda d: -d['d_hotel_metadata_hotrate']['d_hotel_additional_attributes']['f_savings_pct'],
            'f_geographic_distance': lambda d: d['d_hotel_metadata_normal']['d_hotel_additional_attributes']['f_geographic_distance'],
        }
        ld_hotel_metadata_decoded = sorted(ld_hotel_metadata_decoded, key=lambda d: tuple(d_filter_to_get_value[k](d) for k in self.d_hotel_filter))

        # Produce a report
        if b_generate_report:
            if not os.path.isdir('reports'):
                os.makedirs('reports')
            s_pdf_file_path = os.path.join('reports', f'{self.s_report_name}.pdf')
            generate_report_pdf(s_search_query_url, self.d_hotel_filter, ld_hotel_metadata_decoded, s_pdf_file_path)

        # Return hotel metadata and attribute matches
        return ld_hotel_metadata_decoded


def main():

    # Initialize hotwire object, hack, and generate report
    o_hh = HackingHotwire(S_REPORT_NAME, D_HOTEL_FILTER, S_GEOGRAPHIC_GOTO_ADDRESS)
    o_hh.hack_hotwire(S_SEARCH_QUERY_URL, S_HACK_MODE, B_GENERATE_REPORT)


if __name__ == '__main__':
    main()


