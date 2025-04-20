import sys
try:
    from weasyprint import HTML
    HTML('api_test_results.html').write_pdf('api_test_results.pdf')
    print('PDF generated successfully using WeasyPrint!')
    sys.exit(0)
except ImportError:
    try:
        import pdfkit
        pdfkit.from_file('api_test_results.html', 'api_test_results.pdf')
        print('PDF generated successfully using pdfkit!')
        sys.exit(0)
    except ImportError:
        print('Error: Neither WeasyPrint nor pdfkit is installed.')
        print('Install one with: pip install weasyprint or pip install pdfkit')
        sys.exit(1)
