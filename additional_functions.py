

# Do imports
from fpdf import FPDF


def add_query_info_to_report_pdf(o_pdf, s_search_query_url, i_first_line_spacing):

    # Extract key variables
    s_destination = s_search_query_url.split('destination=')[1].split('startDate=')[0][:-1].replace('%20', ' ').replace('%2C', ',')
    s_start_date = s_search_query_url.split('startDate=')[1].split('endDate=')[0][:-1]
    s_end_date = s_search_query_url.split('endDate=')[1].split('rooms=')[0][:-1]
    s_num_rooms = s_search_query_url.split('rooms=')[1].split('adults=')[0][:-1]
    s_num_adults = s_search_query_url.split('adults=')[1].split('children=')[0][:-1]
    s_num_children = s_search_query_url.split('children=')[1]

    # Add query info
    o_pdf.ln(i_first_line_spacing)
    o_pdf.set_font('Helvetica', '', 24)
    o_pdf.cell(w=0, h=0, align='L', txt='Hotwire Query Details')
    o_pdf.ln(10)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Destination:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{s_destination}')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Dates:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{s_start_date}    to    {s_end_date}')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Rooms:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{s_num_rooms}')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Personnel:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{s_num_adults} Adults, {s_num_children} Children')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Hotwire Query URL:')
    o_pdf.set_text_color(0, 0, 255)
    o_pdf.cell(w=0, h=0, align='L', txt='link', link=f'{s_search_query_url}')
    o_pdf.set_text_color(0, 0, 0)


def add_hotel_filter_info_to_report_pdf(o_pdf, d_hotel_filter, i_first_line_spacing):

    # Extract key variables
    f_hotel_class = d_hotel_filter['f_hotel_class']
    f_guest_rating = d_hotel_filter['f_guest_rating']
    f_savings_pct = d_hotel_filter['f_savings_pct']
    f_geographic_distance = d_hotel_filter['f_geographic_distance']

    # Add query info
    o_pdf.ln(i_first_line_spacing)
    o_pdf.set_font('Helvetica', '', 24)
    o_pdf.cell(w=0, h=0, align='L', txt='User Filter Details')
    o_pdf.ln(10)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Hotel Class:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_hotel_class} +')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Guest Rating:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_guest_rating} +')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Savings Percent:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_savings_pct}% +')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Distance:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_geographic_distance} miles or fewer')


def add_hotel_to_report_pdf(o_pdf, d_hotel_metadata_decoded, i_first_line_spacing, i_hotel_num):

    # Extract key variables
    s_hotel_name = d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_additional_attributes']['s_hotel_name'].split(',')[0]
    if len(s_hotel_name) > 40:
        s_hotel_name = f'{s_hotel_name[:30]}...'
    f_hotel_class = d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_comparison_attributes']['f_hotel_class']
    f_guest_rating = d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_comparison_attributes']['f_guest_rating']
    i_list_price = d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_comparison_attributes']['i_list_price']
    i_sale_price = d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_additional_attributes']['i_sale_price']
    f_savings_pct = d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_additional_attributes']['f_savings_pct']
    f_final_price = d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_additional_attributes']['f_final_price']
    f_geographic_distance = d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_additional_attributes']['f_geographic_distance']
    s_geographic_url = d_hotel_metadata_decoded['d_hotel_metadata_normal']['d_hotel_additional_attributes']['s_geographic_url']
    s_hotel_url_normal = d_hotel_metadata_decoded['d_hotel_metadata_normal']['s_hotel_url']
    s_hotel_url_hotrate = d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['s_hotel_url']
    i_hotel_attributes_matched = sum([1 for x in d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_comparison_attributes'].values() if x is not None])
    i_hotel_attributes_total = len(d_hotel_metadata_decoded['d_hotel_metadata_hotrate']['d_hotel_comparison_attributes'].values())

    # Add hotel info
    o_pdf.ln(i_first_line_spacing)
    o_pdf.set_font('Helvetica', '', 24)
    o_pdf.cell(w=0, h=0, align='L', txt=s_hotel_name)
    o_pdf.cell(w=0, h=0, align='R', txt=f'#{i_hotel_num}')
    o_pdf.ln(10)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Class:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_hotel_class}')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Guest Rating:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_guest_rating}')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Savings:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{i_list_price}    --->    {i_sale_price}            ({f_savings_pct}%)')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Final Price:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_final_price}')
    o_pdf.ln(3)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=0, h=0, align='L', txt='-------------------------------------------------------------------------------------------')
    o_pdf.ln(4)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Distance:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{f_geographic_distance}')
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Google Maps URL:')
    o_pdf.set_text_color(0, 0, 255)
    o_pdf.cell(w=0, h=0, align='L', txt='link', link=f'{s_geographic_url}')
    o_pdf.set_text_color(0, 0, 0)
    o_pdf.ln(3)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=0, h=0, align='L', txt='-------------------------------------------------------------------------------------------')
    o_pdf.ln(4)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Normal URL:')
    o_pdf.set_text_color(0, 0, 255)
    o_pdf.cell(w=0, h=0, align='L', txt='link', link=f'{s_hotel_url_normal}')
    o_pdf.set_text_color(0, 0, 0)
    o_pdf.ln(6)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Hotrate URL:')
    o_pdf.set_text_color(0, 0, 255)
    o_pdf.cell(w=0, h=0, align='L', txt='link', link=f'{s_hotel_url_hotrate}')
    o_pdf.set_text_color(0, 0, 0)
    o_pdf.ln(3)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=0, h=0, align='L', txt='-------------------------------------------------------------------------------------------')
    o_pdf.ln(4)
    o_pdf.set_font('Helvetica', '', 14)
    o_pdf.cell(w=80, h=0, align='L', txt='Attributes Matched:')
    o_pdf.cell(w=0, h=0, align='L', txt=f'{i_hotel_attributes_matched}/{i_hotel_attributes_total}')


def generate_report_pdf(s_search_query_url, d_hotel_filter, ld_hotel_metadata_decoded, s_pdf_file, s_letterhead_file='letterhead/Letterhead (Hacking Hotwire) - CROPPED.png'):

    # Define key variables
    i_width = 216
    i_length = 279

    # Initialize fpdf object
    o_pdf = FPDF(format='Letter')

    # Iterate over hotels
    for i_hotel_num, d_hotel_metadata_decoded in enumerate(ld_hotel_metadata_decoded):

        # Add query and filter information to report
        if i_hotel_num == 0:

            # Add page
            o_pdf.add_page()

            # Add letterhead
            o_pdf.image(s_letterhead_file, y=0, x=0, w=i_width)

            # Add query information
            add_query_info_to_report_pdf(o_pdf, s_search_query_url, i_first_line_spacing=80)

            # Add hotel filter information
            add_hotel_filter_info_to_report_pdf(o_pdf, d_hotel_filter, i_first_line_spacing=40)

        # Add hotel to report
        if i_hotel_num % 3 == 0:

            # Add page
            o_pdf.add_page()

            # Add hotel
            add_hotel_to_report_pdf(o_pdf, d_hotel_metadata_decoded, i_first_line_spacing=10, i_hotel_num=i_hotel_num)

        elif i_hotel_num % 3 == 1:

            # Add hotel
            add_hotel_to_report_pdf(o_pdf, d_hotel_metadata_decoded, i_first_line_spacing=28, i_hotel_num=i_hotel_num)

        elif i_hotel_num % 3 == 2:

            # Add hotel
            add_hotel_to_report_pdf(o_pdf, d_hotel_metadata_decoded, i_first_line_spacing=28, i_hotel_num=i_hotel_num)

    # Save report
    o_pdf.output(s_pdf_file)

