from django.shortcuts import render,redirect
from UOM.models import UOM,UOMConversionMatrix

# Create your views here.
def unit_of_measurement(request):
    return render(request,"unit_of_measurement.html")

def uom_register(request):
    if request.method == "POST":
            name = request.POST.get("name").upper().strip()
            description = request.POST.get("description")

            uom = UOM(name=name, description=description)
            uom.save()

            return redirect("UOM:conversion_matrix")
    return redirect("UOM:unit_of_measurement")

def conversion_matrix(request):
     uoms = UOM.objects.all()
     return render(request,"conversion_matrix.html",{'uoms':uoms})

def conversion_register(request):
    if request.method == "POST":
            from_uom_id = request.POST.get("from_uom")
            to_uom_id = request.POST.get("to_uom")
            factor = float(request.POST.get("factor"))

            if from_uom_id == to_uom_id:
                # messages.warning(request, "From and To units must be different.")
                return redirect("UOM:conversion_register")

            from_uom = UOM.objects.get(id=from_uom_id)
            to_uom = UOM.objects.get(id=to_uom_id)

            # Check if already exists (optional)
            existing = UOMConversionMatrix.objects(from_uom=from_uom, to_uom=to_uom).first()
            if existing:
                existing.factor = factor  # update factor if needed
                existing.save()
                # messages.info(request, "Conversion updated successfully.")
            else:
                conversion = UOMConversionMatrix(from_uom=from_uom, to_uom=to_uom, factor=factor)
                conversion.save()
                # messages.success(request, "Conversion added successfully.")

            return redirect("UOM:conversion_register")

    uoms = UOM.objects.all()
    return render(request, "conversion_matrix.html", {"uoms": uoms})