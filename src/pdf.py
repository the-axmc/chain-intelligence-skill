#!/usr/bin/env python3
"""
PDF Report Generator for Chain Intelligence.
Generates 24h market reports as PDFs.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import KeepTogether
from reportlab.pdfgen.canvas import Canvas

from src.analyzer import FundamentalAnalyzer
from src.reporter import MarketReporter


class PDFReportGenerator:
    """Generates comprehensive market analysis PDF reports."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the PDF generator."""
        self.output_dir = output_dir or os.environ.get(
            'OUTPUT_DIR',
            os.path.expanduser('~/.openclaw/workspace-scout/signals/chain-intel/reports')
        )
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.styles = getSampleStyleSheet()
        
        # Custom styles - check if they already exist
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=30
            ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#424242'),
            spaceAfter=12
        ))
        
        if 'SectionTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=12,
                spaceBefore=24
            ))
        
        if 'SubsectionTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubsectionTitle',
                parent=self.styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#37474f'),
                spaceAfter=8,
                spaceBefore=16
            ))
        
        if 'NormalSmall' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='NormalSmall',
                parent=self.styles['Normal'],
                fontSize=9,
                spaceAfter=6
            ))
        
        self.token_colors = {
            'BTC': colors.HexColor('#f57c00'),
            'ETH': colors.HexColor('#673ab7'),
            'LINK': colors.HexColor('#03a9f4'),
            'SOL': colors.HexColor('#4caf50'),
            'AVAX': colors.HexColor('#e91e63'),
            'MATIC': colors.HexColor('#9c27b0'),
        }
    
    def generate_report(self, timeframe: str = '24h', filename: Optional[str] = None) -> str:
        """
        Generate a comprehensive market report PDF.
        
        Args:
            timeframe: Time period to analyze ('1h', '6h', '24h', '7d', '30d')
            filename: Output filename. If None, auto-generates a filename.
            
        Returns:
            Path to the generated PDF file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"chain_intel_report_{timestamp}.pdf"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # Initialize data collectors
        reporter = MarketReporter()
        analyzer = FundamentalAnalyzer()
        
        # Collect data
        print("Collecting market data...")
        metrics = reporter.get_metrics(
            ['BTC', 'ETH', 'LINK', 'SOL', 'AVAX', 'MATIC'],
            timeframe
        )
        
        summary = reporter.get_summary(timeframe)
        analysis = analyzer.analyze_24h()
        
        # Generate PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        
        # Build report sections
        elements.append(self._build_title_section())
        elements.append(Spacer(1, 0.25*inch))
        
        elements.append(self._build_executive_summary(metrics, summary))
        elements.append(PageBreak())
        
        elements.append(self._build_price_action_section(analysis))
        elements.append(PageBreak())
        
        elements.append(self._build_volume_analysis_section(analysis))
        elements.append(PageBreak())
        
        elements.append(self._build_volatility_section(analysis))
        elements.append(PageBreak())
        
        elements.append(self._build_opportunities_section(analysis))
        elements.append(PageBreak())
        
        elements.append(self._build_risks_section(analysis))
        
        # Build PDF
        print(f"Generating PDF...")
        doc.build(elements)
        
        print(f"Report generated: {output_path}")
        return output_path
    
    def _build_title_section(self):
        """Build the title page section."""
        from reportlab.platypus import Image
        
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        elements = [
            Paragraph("Chain Intelligence", self.styles['Title']),
            Paragraph(f"Market Analysis Report - {timestamp}", self.styles['Subtitle']),
            Spacer(1, 1.5*inch),
            Paragraph("Generated automatically by Chain Intelligence", self.styles['NormalSmall']),
        ]
        
        return KeepTogether(elements)
    
    def _build_executive_summary(self, metrics: Dict, summary: Dict):
        """Build the executive summary section."""
        elements = [
            Paragraph("Executive Summary", self.styles['SectionTitle']),
            Spacer(1, 0.25*inch),
        ]
        
        # Summary table
        data = [
            ['Metric', 'Value', 'Change'],
            ['Total Market Cap', f"${summary.get('summary', {}).get('total_market_cap', 0)/1e12:.2f}T", 'N/A'],
            ['Active Tokens', str(summary.get('summary', {}).get('token_count', 0)), 'N/A'],
            ['Gas Price', f"{summary.get('summary', {}).get('gas_price_gwei', 'N/A')} Gwei", 'N/A'],
        ]
        
        # Add token performance
        for token, token_metrics in list(metrics.items())[:3]:
            if 'error' not in token_metrics:
                price_data = token_metrics.get('price', {})
                pct_change = price_data.get('change_24h_pct', 0)
                change_str = f"{pct_change:+.2f}%" if pct_change is not None else "N/A"
                color = 'green' if pct_change and pct_change > 0 else 'red' if pct_change and pct_change < 0 else 'black'
                
                data.append([
                    f"{token} Price",
                    f"${price_data.get('current', 'N/A')}",
                    f'<font color="{color}">{change_str}</font>'
                ])
        
        table = Table(data, colWidths=[1.5*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        
        elements.append(table)
        
        return KeepTogether(elements)
    
    def _build_price_action_section(self, analysis: Dict):
        """Build the price action section."""
        elements = [
            Paragraph("Price Action Analysis", self.styles['SectionTitle']),
            Spacer(1, 0.25*inch),
        ]
        
        price_action = analysis.get('price_action', {})
        
        for token, token_data in price_action.items():
            color = self.token_colors.get(token, colors.black)
            # Use toHex() method for ReportLab Color objects
            color_str = color.toHex() if hasattr(color, 'toHex') else '#000000'
            
            elements.append(Paragraph(f"<font color='{color_str}'>{token}</font>", self.styles['SubsectionTitle']))
            
            data = [
                ['Current Price', f"${token_data['current_price']:.2f}"],
                ['24h Open', f"${token_data['open_24h']:.2f}"],
                ['24h High', f"${token_data['high_24h']:.2f}"],
                ['24h Low', f"${token_data['low_24h']:.2f}"],
                ['24h Change', f"{token_data['price_change_pct']:.2f}%"],
                ['Trend', token_data['price_trend'].upper()],
            ]
            
            table = Table(data, colWidths=[1.5*inch, 3*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.25*inch))
        
        return KeepTogether(elements)
    
    def _build_volume_analysis_section(self, analysis: Dict):
        """Build the volume analysis section."""
        elements = [
            Paragraph("Volume Analysis", self.styles['SectionTitle']),
            Spacer(1, 0.25*inch),
        ]
        
        volume_data = analysis.get('volume_trend', {})
        
        for token, token_data in volume_data.items():
            color = self.token_colors.get(token, colors.black)
            color_str = color.toHex() if hasattr(color, 'toHex') else '#000000'
            
            elements.append(Paragraph(f"<font color='{color_str}'>{token}</font>", self.styles['SubsectionTitle']))
            
            data = [
                ['Current Volume', f"${token_data['current_volume']/1e6:.2f}M"],
                ['24h Average', f"${token_data['average_24h']/1e6:.2f}M"],
                ['24h Change', f"{token_data['volume_change_pct']:.2f}%"],
                ['Trend', token_data['trend'].replace('_', ' ').upper()],
            ]
            
            table = Table(data, colWidths=[1.5*inch, 3*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.25*inch))
        
        return KeepTogether(elements)
    
    def _build_volatility_section(self, analysis: Dict):
        """Build the volatility section."""
        elements = [
            Paragraph("Volatility Analysis", self.styles['SectionTitle']),
            Spacer(1, 0.25*inch),
        ]
        
        volatility_data = analysis.get('volatility', {})
        
        for token, token_data in volatility_data.items():
            color = self.token_colors.get(token, colors.black)
            color_str = color.toHex() if hasattr(color, 'toHex') else '#000000'
            elements.append(Paragraph(f"<font color='{color_str}'>{token}</font>", self.styles['SubsectionTitle']))
            
            data = [
                ['Historical Volatility', f"{token_data['historical_volatility']:.2f}%"],
                ['Current Volatility', f"{token_data['current_volatility']:.2f}%"],
                ['Level', token_data['level'].upper()],
            ]
            
            table = Table(data, colWidths=[1.5*inch, 3*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.25*inch))
        
        return KeepTogether(elements)
    
    def _build_opportunities_section(self, analysis: Dict):
        """Build the opportunities section."""
        elements = [
            Paragraph("Opportunities", self.styles['SectionTitle']),
            Spacer(1, 0.25*inch),
        ]
        
        opportunities = analysis.get('opportunities', [])
        
        if not opportunities:
            elements.append(Paragraph("No opportunities detected in the current market data.", self.styles['NormalSmall']))
            return KeepTogether(elements)
        
        for i, opp in enumerate(opportunities, 1):
            elements.append(Paragraph(f"<b>{i}. {opp['type'].replace('_', ' ').title()}</b>", self.styles['NormalSmall']))
            
            details = [
                f"Asset: {opp['asset']}",
                f"Description: {opp['description']}",
                f"Confidence: {opp.get('confidence', 'unknown').upper()}",
            ]
            
            for detail in details:
                elements.append(Paragraph(f"   • {detail}", self.styles['NormalSmall']))
            
            elements.append(Spacer(1, 0.15*inch))
        
        return KeepTogether(elements)
    
    def _build_risks_section(self, analysis: Dict):
        """Build the risks section."""
        elements = [
            Paragraph("Risks", self.styles['SectionTitle']),
            Spacer(1, 0.25*inch),
        ]
        
        risks = analysis.get('risks', [])
        
        if not risks:
            elements.append(Paragraph("No significant risks detected in the current market data.", self.styles['NormalSmall']))
            return KeepTogether(elements)
        
        for i, risk in enumerate(risks, 1):
            severity = risk.get('severity', 'medium')
            color = 'red' if severity == 'high' else 'orange'
            
            elements.append(Paragraph(f"<b>{i}. <font color='{color}'>{risk['type'].replace('_', ' ').title()}</font></b>", self.styles['NormalSmall']))
            
            details = [
                f"Asset: {risk['asset']}",
                f"Description: {risk['description']}",
                f"Severity: {severity.upper()}",
            ]
            
            for detail in details:
                elements.append(Paragraph(f"   • {detail}", self.styles['NormalSmall']))
            
            elements.append(Spacer(1, 0.15*inch))
        
        return KeepTogether(elements)


def generate_report(timeframe: str = '24h', filename: Optional[str] = None) -> str:
    """Convenience function to generate a report."""
    generator = PDFReportGenerator()
    return generator.generate_report(timeframe, filename)


if __name__ == '__main__':
    # Example usage
    import sys
    
    timeframe = sys.argv[1] if len(sys.argv) > 1 else '24h'
    
    print(f"Generating market report for {timeframe} period...")
    output_path = generate_report(timeframe)
    print(f"Report saved to: {output_path}")
