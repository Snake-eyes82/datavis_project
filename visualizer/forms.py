# visualizer/forms.py
from django import forms
from .models import Dataset

class UploadFileForm(forms.Form):
    name = forms.CharField(max_length=255, required=False, label='Dataset Name (Optional)')
    file = forms.FileField(label='Select an XML File')

class UploadDatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'uploaded_file']

class XMLUploadForm(forms.Form):
    xml_file = forms.FileField(label='Select an XML file')