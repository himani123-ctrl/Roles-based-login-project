
from django.db import connection
from django.shortcuts import render, redirect
# from .forms import MyFormDataForm, ItemForm
from .forms import MyFormDataForm, ItemForm
from myapp.models import MyFormData, Item
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.graphics.shapes import Drawing, Line
from django.core.files.storage import default_storage
from io import BytesIO
from reportlab.lib.units import inch,mm
from django.shortcuts import get_object_or_404
from django.conf import settings

import os

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io


import uuid  # Optional: if you want to use UUIDs for invoice IDs

from .models import ExpenseReport, ExpenseDetail
from .forms import ExpenseReportForm, ExpenseDetailForm
from .models import ExpenseReport
from reportlab.graphics.shapes import Drawing, Line


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import PackageReport, PackageDetail
from .forms import PackageReportForm,PackageDetailForm


@csrf_exempt
def package_report_view(request):
    item_forms = []
    report_id = None 

    if request.method == 'POST':
        report_form = PackageReportForm(request.POST)
        item_count = int(request.POST.get('item_count', 0))  # Default to 1 if not provided

        if report_form.is_valid():
            package_report = report_form.save()
            report_id = package_report.id

            print("Report ID:", report_id)

            for i in range(item_count):
                item_description = request.POST.get(f'item_desc_{i}', '')
                order_quantity = request.POST.get(f'order_quantity_{i}', '')
                shipped_quantity = request.POST.get(f'shipped_quantity_{i}', '')

                if item_description and order_quantity and shipped_quantity:
                    detail = PackageDetail(
                        package_report=package_report,
                        item_description=item_description,
                        order_quantity=int(order_quantity),
                        shipped_quantity=int(shipped_quantity)
                    )
                    detail.save()

            pdf_url = f"/package/report/pdf/{report_id}/"
            return JsonResponse({'success': True, 'pdf_url': pdf_url})

        else:
            # If form is not valid, return errors
            return JsonResponse({'success': False, 'errors': report_form.errors})

            # return redirect('package_report_list_view')  # Update with your actual view name
        # else:
            # Recreate item forms with submitted data for error display
            # item_forms = [PackageDetailForm(request.POST, prefix=f'item_{i}') for i in range(item_count)]
    else:
        report_form = PackageReportForm()
        item_forms = [PackageDetailForm(prefix=f'item_{i}') for i in range(1)]  # Start with one form

    context = {
        'report_form': report_form,
        'item_forms': item_forms,
        'item_count': len(item_forms),
        'report_id': report_id,
    }
    return render(request, 'package_report_form.html', context)


def package_report_list_view(request):
    reports = PackageReport.objects.all()
    return render(request, 'package_report_list.html', {'reports': reports})

def dashboard_view(request):
    return render(request, 'dashboard.html')

@csrf_exempt
def expense_report_view(request):
    item_forms = []
    report_id = None

    if request.method == 'POST':
        report_form = ExpenseReportForm(request.POST)
        item_count = int(request.POST.get('item_count', 0))  # Default to 1 if not provided


      
        if report_form.is_valid():
            expense_report = report_form.save()
            report_id = expense_report.id

            for i in range(item_count):
                expense_description = request.POST.get(f'item_desc_{i}', '')
                merchant = request.POST.get(f'merchant_{i}', '')
                amount = request.POST.get(f'amount_{i}', '')
                date = request.POST.get(f'date_{i}', None)

                if expense_description and merchant and amount and date:
                    detail = ExpenseDetail(
                        expense_report=expense_report,
                        expense_description=expense_description,
                        merchant=merchant,
                        amount=float(amount),
                        date=date
                    )
                    detail.save()


            pdf_url = f"/expense/report/pdf/{report_id}/"
            return JsonResponse({'success': True, 'pdf_url': pdf_url})

        else:
            # If form is not valid, return errors
            return JsonResponse({'success': False, 'errors': report_form.errors})

            # return redirect('expense_report_list_view')
    else:
            # Recreate item forms with submitted data for error display
            # item_forms = [ExpenseDetailForm(request.POST, prefix=f'item_{i}') for i in range(item_count)]
        report_form = ExpenseReportForm()
        item_forms = [ExpenseDetailForm(prefix=f'item_{i}') for i in range(1)]  # Start with one form

    context = {
        'report_form': report_form,
        'item_forms': item_forms,
        'item_count': len(item_forms),
        'report_id': report_id, 
        
    }
    return render(request, 'expense_report_form.html', context)


def expense_report_list_view(request):
    reports = ExpenseReport.objects.all()
    return render(request, 'expense_report_list.html', {'reports': reports})





def form_view(request):
    if request.method == 'POST':
        form_data = MyFormDataForm(request.POST, request.FILES)
        item_count = int(request.POST.get('item_count', 0))
        item_forms = [ItemForm(request.POST, prefix=f'item_{i}') for i in range(item_count)]

        if form_data.is_valid() and all(form.is_valid() for form in item_forms):
            my_form_data = form_data.save(commit=False)
            
            # Generate a unique invoice_id if it's not provided
            if not my_form_data.invoice_id:
                my_form_data.invoice_id = str(uuid.uuid4())  # Generate a new UUID

            my_form_data.save()  # Save the instance to persist the invoice_id
            
            # Delete old items associated with this form
            Item.objects.filter(myformdata=my_form_data).delete()

            # Save each item form with the current form_data instance
            for item_form in item_forms:
                item = item_form.save(commit=False)
                item.myformdata = my_form_data
                item.save()


            return redirect('generate_pdf', invoice_id=my_form_data.invoice_id)
            # Redirect to the list view to see all invoices
            # return redirect('invoice_list_view')
            # return render(request, 'form.html', invoice_id = my_form_data.invoice_id)

    else:
        form_data = MyFormDataForm()
        item_forms = [ItemForm(prefix=f'item_{i}') for i in range(1)]

    invoice_id = form_data.instance.invoice_id if form_data.instance.invoice_id else 'No ID'
  
    context = {
        'form_data': form_data,
        'item_forms': item_forms,
        'item_count': len(item_forms),
        'pdf_available': invoice_id is not None,
        'invoice_id':invoice_id,
        
    }
    return render(request, 'form.html', context)



def invoice_list_view(request):
    invoices = MyFormData.objects.all()
    return render(request, 'invoice_list.html', {'invoices': invoices})

# def generate_pdf(request, invoice_id):
#     my_form_data = get_object_or_404(MyFormData, invoice_id=invoice_id)
#     pdf = generate_pdf(my_form_data)  # Implement this function in your utils
#     response = HttpResponse(pdf, content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'
#     return response

def generate_pdf(request, invoice_id):

    print(u"\u20B9")
    rupee_symbol = u"\u20B9"

    # Get the invoice data
    data = get_object_or_404(MyFormData, invoice_id=invoice_id)
    items = data.items.all()


    font_path = os.path.join(settings.BASE_DIR,'myapp', 'static', 'fonts', 'ITFRupee.ttf')
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('ITFRupee',font_path))
    else:
        return HttpResponse("Font file not found", status=404)
    
    def format_amount(amount):
        return Paragraph(f"<font name='ITFRupee'>R</font>{amount}")
    
    def format_currency(value):
        if value is not None:
            return format_amount(value)
        return format_amount("0.00")
    
    def format_paragraph(text):
        return Paragraph(text, normal_style)
   
    

    # def format_datetime(dt):
    #     return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else 'N/A'
    def format_datetime(dt):
       return dt.strftime('%d %b %Y') if dt else 'N/A'



    # def format_currency(value):
    #     return f"₹{value:,.2f}" if value is not None else "₹0.00"

    def format_percentage(value):
        return f"{value:.2f}%" if value is not None else "0.00%"

    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=10, leftMargin=10, topMargin=30, bottomMargin=18)

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.fontSize = 20
    title_style.alignment = 1

    normal_style = styles['Normal']
    normal_style.fontSize = 10

    

    logo = None
    if data.logo:
        logo_path = default_storage.path(data.logo.name)
        logo = Image(logo_path, width=2*inch, height=1*inch)
        logo.hAlign = 'LEFT'


    title_style = styles['Heading1']
    title_style.fontSize =30  # Original font size
    title_style.alignment = 1

    title = Paragraph("TAX INVOICE", title_style)


    logo_and_title = []
    if logo:
        logo_and_title.append([logo, title])
    else:
        logo_and_title.append([None, title])

    logo_title_table = Table(logo_and_title)
    logo_title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
    ]))


    bold_style = styles['Normal']
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.fontSize = 12

    company_info = [
        # [Paragraph("<b>Company Details:</b>", bold_style), ""],
        ["", data.company],
        ["", data.your_name],
        ["", data.company_gstin],
        ["", data.company_address],
        ["", data.city],
        ["", data.state],
        ["", data.country],
    ]

    company_table = Table(company_info, colWidths=[10*mm,207*mm,220*mm])
    company_table.setStyle(TableStyle([
       
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))


    bold_style = styles['Normal']
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.fontSize = 10

    client_info = [
        [Paragraph("<b>Bill To:</b>", bold_style),""],
        [data.client_company,"","Invoice#", data.invoice],
        [data.client_gstin,"","Invoice Date", format_datetime(data.datetime_field1)],
        [data.client_address,"","Due Date", format_datetime(data.datetime_field2)],
        [data.client_city],
        [data.client_country],
        [data.client_state],
        # ["Place of supply:",data.client_country],
        # ["Invoice#", data.invoice],
        # ["Invoice Date", format_datetime(data.datetime_field1)],
        # ["Due Date", format_datetime(data.datetime_field2)],
    ]

    client_table = Table(client_info, colWidths=[48*mm,65*mm, 40*mm])
    client_table.setStyle(TableStyle([
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))

    item_data = [["Item Desc", "Quantity", "Rate","Gst rate","Cess", "Amount", "SGST","CGST","Total"]]
    
    total_amount = 0
    total_sgst = 0
    total_cgst = 0
    total = 0
    tot_sgst=0
    tot_cgst=0

  
    
    for item in items:
        amount = item.qty * item.rate
        # sgst_amount = (item.sgst / 100) * amount
        # cgst_amount = (item.cgst / 100) * amount
        tot_sgst=(item.gst_rate/2)
        tot_cgst=(item.gst_rate/2)
        sgst_amount = (tot_sgst / 100) * amount
        cgst_amount = (tot_cgst / 100) * amount
        # cgst_amount = (item.cgst / 100) * amount
        cess_amount = item.cess
        tot_gst=sgst_amount+cgst_amount 
        item_total = amount + sgst_amount + cgst_amount + cess_amount
        
        total_amount += amount
        total_sgst += sgst_amount
        total_cgst += cgst_amount
        total+=item_total
       
 
        
        item_data.append([
            item.item_desc,
            str(item.qty or 0),
            format_currency(item.rate),
            format_percentage(item.gst_rate),
            format_percentage(item.cess),
            format_currency(amount),
            format_currency(tot_sgst),
            format_currency(tot_cgst),
            format_currency(item_total),
          
            
        ])

    item_table = Table(item_data, colWidths=[20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm,20*mm,20*mm])
    # item_table = Table(item_data, colWidths=[25*mm] * len(item_data[0]))

    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        # ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.black),  
        ('PAD', (0, 1), (-1, -1), 15),
    ]))

    total_info = [
        ["", "", "", "", "", "","Grand Total", format_currency(total)],
        ["", "", "", "", "", ""],
        #  ["", "", "", "", "", ""],
      
    ]

    # total_table = Table(total_info, colWidths=[90*mm, 20*mm, 30*mm, 30*mm, 30*mm, 30*mm, 50*mm])
    total_table = Table(total_info, colWidths=[60*mm,10*mm,10*mm,10*mm,15*mm,16*mm,40*mm,30*mm])
    total_table.setStyle(TableStyle([
        # ('SPAN', (0, 0), (5, 0)),
        # ('SPAN', (0, 1), (5, 1)),
        # ('SPAN', (0, 2), (5, 2)),
        # ('ALIGN', (6, 0), (6, 2), 'RIGHT'),
        # ('ALIGN', (6, 3), (6, 3), 'RIGHT'),
        # ('BACKGROUND', (6, 3), (6, 3), colors.lightgrey),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.black),  
        
        
        # Remove grid from other rows if any
        
        ('BACKGROUND', (6, 0), (7, 0), colors.lightgrey),
        ('ALIGN', (6, 0), (6, 3), 'RIGHT'),
        ('ALIGN', (7, 0), (7, 3), 'RIGHT'),
       
       
    
    ]))
    bold_style = styles['Normal']
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.fontSize = 10


    # notes = [
    #     [Paragraph("<b>Notes:</b>"), ""," "],
    #     ["It was great doing business with you."],
    #     ["Terms & Conditions"],
    #     ["Please make the payment by the due date."],
    # ]
   
    notes = [
        [Paragraph("Notes:", normal_style), "", " "],
        [data.notes or "No notes available."],
        [Spacer(1, 12)],
        [Paragraph("Terms & Conditions:", normal_style), "", " "],
        [data.terms_conditions or "No terms and conditions provided."]
    ]
    notes_table = Table(notes, colWidths=[45*mm, 22*mm, 130*mm])

    elements = [
        logo_title_table, 
        Spacer(1, 12),
        company_table,
        Spacer(1, 24),
        client_table,
        Spacer(1, 36),
        item_table,
        Spacer(1, 24),
        total_table,
        Spacer(1,24),
        notes_table,
    ]
    pdf.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'
    return response


def calculate_totals(data):
    total_amount = data.amount
    total_sgst = data.sgst
    total_cgst = data.cgst
    total = total_sgst + total_cgst + total_amount
    return total, total_amount, total_sgst, total_cgst

def generate_expense_report_pdf(request, report_id):
    # Fetch the expense report
    report = get_object_or_404(ExpenseReport, id=report_id)
    details = report.details.all()  # Use the related name to get expense details

    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    font_path = os.path.join(settings.BASE_DIR,'myapp', 'static', 'fonts', 'ITFRupee.ttf')
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('ITFRupee',font_path))
    else:
        return HttpResponse("Font file not found", status=404)

    def format_amount(amount):
        return Paragraph(f"<font name='ITFRupee'>R</font>{amount}")
    
    def format_currency(value):
        if value is not None:
            return format_amount(value)
        return format_amount("0.00")

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

  
    # right_aligned_style = ParagraphStyle(name='RightAligned', parent=styles['Title'], alignment=1) 
    right_aligned_normal_style = ParagraphStyle(name='RightAlignedNormal', parent=normal_style, alignment=1,fontSize=20)

    company_name_style = ParagraphStyle(name='CompanyNameStyle', parent=normal_style, fontSize=14)
    
    right_aligned_small_style = ParagraphStyle(name='RightAlignedSmall', parent=normal_style, alignment=1, fontSize=11)
    

    title = Paragraph("", right_aligned_normal_style)
    elements.append(title)

    styles = getSampleStyleSheet()
    # bold_style = styles['Normal']
    # bold_style.fontName = 'Helvetica-Bold'
    # bold_style.fontSize = 12



    report_details = [
        ["",  Paragraph(report.company_name, company_name_style),Paragraph("Expense Report", right_aligned_normal_style)],
        ["", "", ""],
        ["", report.your_name,Paragraph(report.city,  right_aligned_small_style)],
        ["", report.company_address,""],
        # ["", report.city,""],
        ["", report.country,""],

    ]
         

   
    report_table = Table(report_details, colWidths=[0.4 * inch, 5 * inch,3* inch])
    report_table.setStyle(TableStyle([
        # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.lightgrey), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (1, 0), (-1, 0), 0), 
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0), 
        ('LEFTPADDING', (2, 2), (2, 2), 110)
        
      
    ]))

    elements.append(report_table)
    elements.append(Spacer(1, 0.3 * inch))


    line_width = 480  # Total length of the line
    line_length_increase = 45  # Amount to increase length on the left
    line_drawing = Drawing(line_width + line_length_increase, 1)  # Width, height
    line = Line(-line_length_increase, 0, line_width, 0)  # Adjust starting point to move left
    line.strokeColor = colors.grey  # Set the line color
    line_drawing.add(line)  # Add line to the drawing
    elements.append(line_drawing)  # Add drawing to elements

    elements.append(Spacer(1, 0.1 * inch))
         
    styles = getSampleStyleSheet()
    bold_style = styles['Normal']
    bold_style.fontName = 'Helvetica-Bold'

    report_dates = [
    ["", "", ""],
    [Paragraph("Meeting To Mumbai", bold_style), Paragraph("From:", bold_style), ""],
    [report.state, report.report_from,""],
    ["", "", ""],
    ["", Paragraph("To:", bold_style), Paragraph("Report Period:", bold_style)],
    ["", report.report_to,f"{report.date_from.strftime('%b %d, %Y')} - {report.date_to.strftime('%b %d, %Y')}"],
  
]

# Create a table for report dates with three columns
    date_table = Table(report_dates, colWidths=[3.2* inch, 2.3 * inch, 2 * inch])
    date_table.setStyle(TableStyle([
    # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    # ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
   

    elements.append(date_table)
    elements.append(Spacer(1, 0.5 * inch))

    item_data = [["Date", "Description", "Merchant", "Amount"]]

    for detail in details:
        item_data.append([
            detail.date.strftime('%Y-%m-%d'),
            detail.expense_description,
            detail.merchant,
            format_currency(detail.amount),
        ])
        
    total_amount = sum(detail.amount for detail in details)

    styles = getSampleStyleSheet()
    bold_style = styles['Normal']
    bold_style.fontName = 'Helvetica-Bold'

# Add a row for the total amount only after all details
    item_data.append(["", "", "Total:", format_currency(total_amount)])


    col_widths = [2.1* inch, 2.2* inch, 2 * inch, 1 * inch]  # Adjust the widths as needed

       

# Create a table for the expense details with specified column widths
    item_table = Table(item_data, colWidths=col_widths)

    # Create a table for the expense details
    # item_table = Table(item_data)
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black), # Black background for the header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), 
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Default background
        ('TOPPADDING', (0, 0), (-1, -1), 8),  # Increase top padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),  # Increase bottom padding
       

    ]))
       

    elements.append(item_table)
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Spacer(1, 0.5 * inch))

    line_width = 480  # Total length of the line
    line_length_increase = 39  # Amount to increase length on the left

# Create a drawing for the lines
    line_drawing = Drawing(line_width + line_length_increase, 1)  # Width, height

# Create left line (up to 3 inches)
    left_line_length = 1.2 * inch  # 3 inches
    left_line = Line(-line_length_increase, 0, left_line_length, 0)  # Adjust starting point
    left_line.strokeColor = colors.grey  # Set the line color
    line_drawing.add(left_line)  # Add left line to the drawing

# Create right line (from 3 inches to the end)
    right_line_start = left_line_length + 40  # Space after left line
    right_line_length = 3.6 * inch 
    right_line = Line(right_line_start, 0, right_line_length, 0)  # Right line
    right_line.strokeColor = colors.grey  # Set the line color
    line_drawing.add(right_line)  # Add right line to the drawing

# Add drawing to elements
    elements.append(line_drawing)


    approval_data = [
        [Paragraph("Submitted By", bold_style), Paragraph("Approved By", bold_style),""],
        [Paragraph(report.report_from, normal_style), Paragraph(report.report_to, normal_style,"")],
    ]

    approval_table = Table(approval_data, colWidths=[ 2.3* inch, 3.4* inch,1.4*inch])
    approval_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        # ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(approval_table)

    # Build the PDF
    pdf.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="expense_report_{report_id}.pdf"'
    return response

def generate_package_report_pdf(request, report_id):
    # Fetch the package report
    report = get_object_or_404(PackageReport, id=report_id)
    details = report.details.all()  # Use the related name to get package details

    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, topMargin=10)
    elements = []
    
    font_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'fonts', 'ITFRupee.ttf')
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('ITFRupee', font_path))
    else:
        return HttpResponse("Font file not found", status=404)

    def format_amount(amount):
        return Paragraph(f"<font name='ITFRupee'>R</font>{amount:.2f}")

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    bold_style = styles['Normal']
    bold_style.fontName = 'Helvetica-Bold'
    
  

    company_name_style = ParagraphStyle(name='CompanyNameStyle', fontSize=12, leading=14)  # Smaller font for company name
    title_style = ParagraphStyle(name='TitleStyle', fontSize=20, leading=28)  # Larger font for title

    company_details = [
    [Paragraph(report.company_name, company_name_style), "", Paragraph("PACKING SLIP", title_style)],
    [report.your_name,""],
    [report.city,""],
    [report.state,""],
    [report.country,""],
]

    company_table = Table(company_details, colWidths=[2.2 * inch, 3.2* inch,2.3*inch])
    company_table.setStyle(TableStyle([
    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
     
    company_details[0][1] = Paragraph("Company Name:", normal_style)
    elements.append(company_table)
    elements.append(Spacer(1, 0.5 * inch))  # Spacer between tables


    bold_style = styles['Normal']
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.fontSize = 10

   
# Client details and sales order table
    client_details = [
    [Paragraph("<b>Bill To:</b>", bold_style),""],
    [report.client_name,"","Package#", report.package],
    [report.client_city,"","Order Date", report.order_date.strftime('%Y-%m-%d')],
    [report.client_state,"","Package Date", report.package_date.strftime('%Y-%m-%d')],
    [report.client_country,"","Sales Order#", report.sales_order],
   
   
]

    client_table = Table(client_details, colWidths=[2.3 * inch,2.4*inch, 1.5 * inch])
    client_table.setStyle(TableStyle([
    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))

    elements.append(client_table)

    # Item details table
    item_data = [[" Item Description", "Order Quantity", "Shipped Quantity"]]
    total_order_quantity = 0
    total_shipped_quantity = 0
    for detail in details:
        item_data.append([
            detail.item_description,
            detail.order_quantity,
            detail.shipped_quantity,
        ])
        total_order_quantity += detail.order_quantity
        total_shipped_quantity += detail.shipped_quantity
    
    item_data.append([
    "TOTAL",
    total_order_quantity,
    total_shipped_quantity,
])
    elements.append(Spacer(1, 0.5 * inch)) 


    row_heights = [0.4 * inch] * len(item_data) 
    item_table = Table(item_data, colWidths=[4.2 * inch, 1.7 * inch, 1.7* inch], rowHeights=row_heights)
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),  
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  
        ('ALIGN', (0, -1), (0, -1), 'RIGHT'),   
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),           # Center-align header for Order Quantity
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),   
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),          # Center-align Order Quantity column data
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),   
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header font
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Normal font for other rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Set background for rows
        # ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Total row background
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),  # Total row text color
        ('BOLD', (0, -1), (-1, -1)),  # Bold total row
  
    ]))

    elements.append(item_table)

    elements.append(Spacer(1, 0.2 * inch)) 
    elements.append(Spacer(1, 0.2 * inch)) 

    notes_title = "Notes:"  # Title for the notes section
    notes_content = report.notes if report.notes else ""  # Use report.notes

# Create a table for the notes with the title and content in two rows
    notes_table_data = [
    [Paragraph(notes_title, bold_style),"",""],  # Title row
    [Paragraph(notes_content),"",""]  # Content row
]
    notes_table = Table(notes_table_data, colWidths=[2 * inch,5.2*inch,0.5*inch])  # Adjust width as needed

# Apply styles to the notes table
    notes_table.setStyle(TableStyle([
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),   # Title text color
    ('ALIGN', (0, 0), (0, 0), 'LEFT'),               # Left-align the title
    ('ALIGN', (0, 1), (0, 1), 'LEFT'),               # Left-align the notes content
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),             # Align text to the top
     # Add grid lines
]))

# Add the notes table to elements
    elements.append(notes_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Build the PDF
    pdf.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="package_report_{report_id}.pdf"'
    return response









    # elements = []
    # if logo:
    #     elements.append(logo)
    # elements.extend([
    #     logo_title_table, 
    #     Spacer(1, 6),
    #     company_table,
    #     Spacer(1, 12),
    #     client_table,
    #     Spacer(1, 12),
    #     item_table,
    #     Spacer(1, 12),
    #     total_table,
    #     Spacer(1, 12),
    #     notes_table,
    # ])













# 
# # # views.py
# from django.shortcuts import render, redirect
# from .forms import MyFormDataForm, ItemForm
# from .models import MyFormData, Item
# from django.http import HttpResponse
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
# from django.core.files.storage import default_storage
# from io import BytesIO
# from reportlab.lib.units import inch,mm
# from django.shortcuts import get_object_or_404

# def form_view(request):
#     if request.method == 'POST':
#         form_data = MyFormDataForm(request.POST)
#         item_count = int(request.POST.get('item_count', 0))
#         item_forms = [ItemForm(request.POST, prefix=f'item_{i}') for i in range(item_count)]

#         if form_data.is_valid() and all(form.is_valid() for form in item_forms):
#             my_form_data = form_data.save()
            
#             Item.objects.filter(myformdata=my_form_data).delete()  
            
#             for item_form in item_forms:
#                 item = item_form.save(commit=False)
#                 item.myformdata = my_form_data
#                 item.save()

            
#             return redirect('form_view')  

#     else:
#         form_data = MyFormDataForm()
#         item_forms = [ItemForm(prefix=f'item_{i}') for i in range(1)]  

#     context = {
#         'form_data': form_data,
#         'item_forms': item_forms,
#         'item_count': len(item_forms),
        
#     }
#     return render(request, 'form.html', context)



# def generate_pdf(invoice_id):
#     def format_datetime(dt):
#         if dt:
#             return dt.strftime('%Y-%m-%d %H:%M:%S')  # Adjust format as needed
#         return 'N/A'

#     def format_currency(value):
#         if value is not None:
#             return f"₹{value:,.2f}"  
#         return "₹0.00"

#     def format_percentage(value):
#         if value is not None:
#             return f"{value:.2f}%"  
#         return "0.00%"


#     # try:
#     #     data = MyFormData.objects.get(pk=invoice_id)
#     # except MyFormData.DoesNotExist:
#     #     return HttpResponse("Data not found", status=404)
    

#     # response = HttpResponse(content_type='application/pdf')
#     # response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'

   
#     data = get_object_or_404(MyFormData, pk=invoice_id)
#     # Create a file-like buffer to receive PDF data
#     buffer = BytesIO()
#     pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=10, leftMargin=0, topMargin=30, bottomMargin=18)

#     styles = getSampleStyleSheet()
#     title_style = styles['Heading1']
#     title_style.fontSize = 20
#     title_style.alignment = 1

#     normal_style = styles['Normal']
#     normal_style.fontSize = 10

#     logo = None
#     if data.logo:
#         logo_path = default_storage.path(data.logo.name)
#         logo = Image(logo_path, width=1*inch, height=1*inch)
#         logo.hAlign = 'LEFT'

#     title = Paragraph("TAX INVOICE", title_style)

#     company_info = [
#         ["Company details:"],
#         ["Company Name ", data.company],
#         ["Your Name ", data.your_name],
#         ["Company GSTIN ", data.company_gstin],
#         ["Company Address", data.company_address],
#         ["City", data.city],
#         ["State", data.state],
#         ["Country", data.country],
#     ]

#     company_table = Table(company_info, colWidths=[50*mm, 10*mm, 5*mm, 10*mm, 20*mm])
#     company_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('RIGHTPADDING', (0, 0), (-1, -1), 5),
#     ]))

#     client_info = [
#         ["Bill To:", ""],
#         ["Client company", data.client_company],
#         ["Client gstin", data.client_gstin],
#         ["Client address", data.client_address],
#         ["Client City", data.client_city],
#         ["Client State", data.client_state],
#         ["Client Country", data.client_country],
#         ["Invoice#", data.invoice],
#         ["Invoice Date", format_datetime(data.datetime_field1)],
#         ["Due Date", format_datetime(data.datetime_field2)],
#     ]

#     client_table = Table(client_info, colWidths=[80*mm, 30*mm, 20*mm])
#     client_table.setStyle(TableStyle([
#         ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
#         ('LEFTPADDING', (0, 0), (-1, -1), -0)
#     ]))

#     item_data = [
#         ["Item Desc", "Qty", "Rate", "SGST", "CGST", "Cess", "Amount", "Total"],
#         [data.item_desc, str(data.qty or 0), format_currency(data.rate),
#          format_percentage(data.sgst), format_percentage(data.cgst), format_currency(data.cess),
#          format_currency(data.amount),
#          format_currency(data.amount + data.sgst + data.cgst)]
#     ]

#     item_table = Table(item_data, colWidths=[20*mm, 10*mm, 20*mm, 18*mm, 18*mm, 18*mm, 25*mm])
#     item_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#     ]))

#     total, total_amount, total_sgst, total_cgst = calculate_totals(data)
#     total_info = [
#         ["", "", "Sub Total", "", "", "", format_currency(total_amount)],
#         ["", "", "SGST", "", "", "", format_currency(total_sgst)],
#         ["", "", "CGST", "", "", "", format_currency(total_cgst)],
#         ["", "", "", "", "", "", format_currency(total)],
#     ]

#     total_table = Table(total_info, colWidths=[90*mm, 20*mm, 30*mm, 30*mm, 30*mm, 30*mm, 50*mm])
#     total_table.setStyle(TableStyle([
#         ('SPAN', (0, 0), (5, 0)),
#         ('SPAN', (0, 1), (5, 1)),
#         ('SPAN', (0, 2), (5, 2)),
#         ('ALIGN', (6, 0), (6, 2), 'RIGHT'),
#         ('ALIGN', (6, 3), (6, 3), 'RIGHT'),
#         ('BACKGROUND', (6, 3), (6, 3), colors.lightgrey),
#     ]))

#     notes = [
#         ["Notes"],
#         ["It was great doing business with you."],
#         ["Terms & Conditions"],
#         ["Please make the payment by the due date."],
#     ]

#     notes_table = Table(notes)
#     notes_table.setStyle(TableStyle([
#         ('SPAN', (0, 0), (-1, 0)),
#         ('SPAN', (0, 1), (-1, 1)),
#         ('SPAN', (0, 2), (-1, 2)),
#         ('SPAN', (0, 3), (-1, 3)),
#         ('ALIGN', (0, 0), (0, 3), 'LEFT'),
#     ]))

#     elements = []
#     if logo:
#         elements.append(logo)
#     elements.extend([
#         Spacer(1, 12),
#         title,
#         Spacer(1, 12),
#         company_table,
#         Spacer(1, 12),
#         client_table,
#         Spacer(1, 12),
#         item_table,
#         Spacer(1, 12),
#         total_table,
#         Spacer(1, 12),
#         notes_table,
#     ])

#     pdf.build(elements)


#     # buffer.seek(0)

#     # response = HttpResponse(buffer, content_type='application/pdf')
#     # response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'

#     # return response

#     # buffer.seek(0)
#     # file_path = f'invoice_{invoice_id}.pdf'
#     # with default_storage.open(file_path, 'wb') as f:
#     #     f.write(buffer.getvalue())

#     # buffer.close()

#     buffer.seek(0)
#     response = HttpResponse(buffer, content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'
#     return response

# def calculate_totals(data):
#     total_amount = data.amount
#     total_sgst = data.sgst
#     total_cgst = data.cgst
#     total = total_sgst + total_cgst + total_amount
#     return total, total_amount, total_sgst, total_cgst