from flask import Blueprint, render_template, request,flash,redirect, url_for
from flask_login import login_required, current_user
from models import CountyAverages, Farmer, RainfallData, CropHealth, SoilHealth, Officer, FarmRecord, Crop, Advisory
from sqlalchemy import func, case
from datetime import datetime, date, timedelta
from extensions import db
from flask_login import current_user, login_required

officer_bp = Blueprint('officer', __name__,url_prefix='/officer')

@officer_bp.route('/dashboard')
@login_required
def officer_dashboard():
    if current_user.role != 'officer':
        return "Unauthorized", 403
    
    # Get selected county from query params
    selected_county = request.args.get('county', '')
    selected_period = request.args.get('period', 'all')  # 'all', 'this_year', 'last_30_days', 'custom'
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Base queries with county filter
    farmers_query = Farmer.query
    if selected_county:
        farmers_query = farmers_query.filter_by(county=selected_county)

    farmers = farmers_query.all()
    farmer_ids = [f.id for f in farmers]

    # Total farmers count
    total_farmers = len(farmer_ids)

    # Apply date filter to FarmRecord
    farm_record_query = FarmRecord.query.filter(FarmRecord.farmer_id.in_(farmer_ids)) if farmer_ids else None

    # Apply period filter
    today = datetime.now().date()
    if selected_period == 'this_year':
        start_date_filter = date(today.year, 1, 1)
        end_date_filter = today
        if farm_record_query:
            farm_record_query = farm_record_query.filter(FarmRecord.harvest_date >= start_date_filter)
    elif selected_period == 'last_30_days':
        start_date_filter = today - timedelta(days=30)
        end_date_filter = today
        if farm_record_query:
            farm_record_query = farm_record_query.filter(FarmRecord.harvest_date >= start_date_filter)
    elif selected_period == 'custom' and start_date and end_date:
        if farm_record_query:
            farm_record_query = farm_record_query.filter(
                FarmRecord.harvest_date >= datetime.strptime(start_date, '%Y-%m-%d').date(),
                FarmRecord.harvest_date <= datetime.strptime(end_date, '%Y-%m-%d').date()
            )

    # PER CROP YIELD KPI 
    per_crop_yield = []
    top_crop = {'name': 'N/A', 'yield': 0, 'percentage': 0}
    total_period_yield = 0

    if farmer_ids and farm_record_query:
        # Get yield per crop for the selected period with farmer count
        crop_yield_data = db.session.query(
            Crop.crop_name,
            func.sum(FarmRecord.yield_kg).label('total_yield'),
            func.count(FarmRecord.farmer_id.distinct()).label('farmer_count')
        ).join(FarmRecord, Crop.id == FarmRecord.crop_id)\
         .filter(FarmRecord.id.in_([r.id for r in farm_record_query.all()]))\
         .group_by(Crop.crop_name)\
         .order_by(func.sum(FarmRecord.yield_kg).desc())\
         .all()

        total_period_yield = sum(y[1] for y in crop_yield_data)

        # Calculate previous period dates for trend comparison
        prev_start = None
        prev_end = None
        if selected_period == 'this_year':
            prev_start = date(today.year - 1, 1, 1)
            prev_end = date(today.year - 1, 12, 31)
        elif selected_period == 'last_30_days':
            prev_start = today - timedelta(days=60)
            prev_end = today - timedelta(days=31)

        # Format for display with all calculated fields
        per_crop_yield = []
        for y in crop_yield_data:
            crop_name = y[0]
            crop_total = y[1]
            farmer_count = y[2]

            # Calculate trend if previous period exists
            trend = 'flat'
            trend_percentage = 0
            if prev_start and prev_end:
                # Get the crop ID first
                crop_id = db.session.query(Crop.id).filter(Crop.crop_name == crop_name).scalar()

                if crop_id:
                    prev_yield = db.session.query(func.sum(FarmRecord.yield_kg))\
                    .filter(
                        FarmRecord.farmer_id.in_(farmer_ids),
                        FarmRecord.crop_id == crop_id,
                        FarmRecord.harvest_date >= prev_start,
                        FarmRecord.harvest_date <= prev_end
                    ).scalar() or 0

                    if prev_yield > 0:
                        change = ((crop_total - prev_yield) / prev_yield) * 100
                        trend = 'up' if change > 0 else 'down' if change < 0 else 'flat'
                        trend_percentage = round(abs(change), 1)

            per_crop_yield.append({
                'crop': crop_name,
                'yield': round(crop_total, 1),
                'percentage': round((crop_total / total_period_yield * 100), 1) if total_period_yield > 0 else 0,
                'avg_per_farmer': round(crop_total / farmer_count, 1) if farmer_count > 0 else 0,
                'farmer_count': farmer_count,
                'trend': trend,
                'trend_percentage': trend_percentage
            })

        # Get top crop
        if crop_yield_data:
            top_crop = {
                'name': crop_yield_data[0][0],
                'yield': round(crop_yield_data[0][1], 1),
                'percentage': round((crop_yield_data[0][1] / total_period_yield * 100), 1) if total_period_yield > 0 else 0
            }

    # PERIOD COMPARISON 
    # Compare with previous period
    comparison = {}
    if selected_period != 'all' and farmer_ids:
        # Get previous period dates
        if selected_period == 'this_year':
            prev_start = date(today.year - 1, 1, 1)
            prev_end = date(today.year - 1, 12, 31)
        elif selected_period == 'last_30_days':
            prev_start = today - timedelta(days=60)
            prev_end = today - timedelta(days=31)
        else:
            prev_start = None
            prev_end = None

        if prev_start and prev_end:
            # Get previous period yield
            prev_yield = db.session.query(func.sum(FarmRecord.yield_kg))\
                .filter(
                    FarmRecord.farmer_id.in_(farmer_ids),
                    FarmRecord.harvest_date >= prev_start,
                    FarmRecord.harvest_date <= prev_end
                ).scalar() or 0

            # Calculate change
            if prev_yield > 0:
                change = ((total_period_yield - prev_yield) / prev_yield) * 100
            else:
                change = 100 if total_period_yield > 0 else 0

            comparison = {
                'previous_yield': round(prev_yield, 1),
                'change': round(change, 1),
                'trend': 'up' if change > 0 else 'down' if change < 0 else 'flat'
            }

    # ========== FIX 1: Total Crops ==========
    # Count unique crops grown by farmers (not just crop IDs in FarmRecord)
    total_crops = db.session.query(Crop.id)\
        .join(FarmRecord, Crop.id == FarmRecord.crop_id)\
        .filter(FarmRecord.farmer_id.in_(farmer_ids))\
        .distinct().count() if farmer_ids else 0

    # ========== FIX 2: Active Health Issues (Latest only) ==========
    active_issues = 0
    if farmer_ids:
        # Get the latest health status for each crop per farmer
        latest_statuses = db.session.query(
            CropHealth.health_status
        ).filter(
            CropHealth.id.in_(
                db.session.query(
                    func.max(CropHealth.id)
                ).filter(CropHealth.farmer_id.in_(farmer_ids))
                 .group_by(CropHealth.farmer_id, CropHealth.crop_id)
            )
        ).all()

        # Count only those with Poor or Fair status
        active_issues = sum(1 for status, in latest_statuses if status in ['Poor', 'Fair'])

    # ========== FIX 3: Latest Health Table (One row per farmer) ==========
    # Show the most critical/urgent issue per farmer (prioritize Poor > Fair > Healthy)
    latest_health = []
    if farmer_ids:
        # Get all latest crop health records per farmer
        farmer_crop_status = {}

        # Subquery to get latest date for each farmer's crop
        latest_dates = db.session.query(
            CropHealth.farmer_id,
            CropHealth.crop_id,
            func.max(CropHealth.date).label('latest_date')
        ).filter(CropHealth.farmer_id.in_(farmer_ids))\
         .group_by(CropHealth.farmer_id, CropHealth.crop_id)\
         .subquery()

        # Get full records for latest dates
        all_latest = db.session.query(
            Farmer.id,
            Farmer.full_name,
            Farmer.county,
            Crop.crop_name,
            CropHealth.health_status,
            CropHealth.date,
            CropHealth.id.label('crop_health_id')
        ).join(
            latest_dates,
            (CropHealth.farmer_id == latest_dates.c.farmer_id) &
            (CropHealth.crop_id == latest_dates.c.crop_id) &
            (CropHealth.date == latest_dates.c.latest_date)
        ).join(Farmer, Farmer.id == CropHealth.farmer_id)\
         .join(Crop, Crop.id == CropHealth.crop_id)\
         .order_by(CropHealth.date.desc())\
         .all()

        # For each farmer, keep the most critical issue (Poor > Fair > Healthy)
        for record in all_latest:
            farmer_id = record[0]

            # Priority: Poor > Fair > Healthy
            priority = {'Poor': 3, 'Fair': 2, 'Healthy': 1}
            current_priority = priority.get(record[4], 0)

            if farmer_id not in farmer_crop_status:
                farmer_crop_status[farmer_id] = record
            else:
                existing_priority = priority.get(farmer_crop_status[farmer_id][4], 0)
                if current_priority > existing_priority:
                    farmer_crop_status[farmer_id] = record

        # Convert back to list
        latest_health = list(farmer_crop_status.values())

    # Total yield (sum of all yields from farmers in selected county)
    total_yield = db.session.query(func.sum(FarmRecord.yield_kg))\
        .filter(FarmRecord.farmer_id.in_(farmer_ids))\
        .scalar() or 0

    # Yield per crop for chart (filtered by county)
    yield_data = db.session.query(
        Crop.crop_name,
        func.sum(FarmRecord.yield_kg).label('total_yield')
    ).join(FarmRecord, Crop.id == FarmRecord.crop_id)\
     .filter(FarmRecord.farmer_id.in_(farmer_ids))\
     .group_by(Crop.crop_name)\
     .all() if farmer_ids else []

    crop_names = [y[0] for y in yield_data]
    crop_yields = [float(y[1]) for y in yield_data]

    # Health distribution for pie chart (latest status per crop per farmer)
    health_counts = {'Healthy': 0, 'Fair': 0, 'Poor': 0}

    if farmer_ids:
        # Get latest health status for each crop per farmer
        latest_statuses = db.session.query(
            CropHealth.health_status
        ).filter(
            CropHealth.id.in_(
                db.session.query(
                    func.max(CropHealth.id)
                ).filter(CropHealth.farmer_id.in_(farmer_ids))
                 .group_by(CropHealth.farmer_id, CropHealth.crop_id)
            )
        ).all()

        for status, in latest_statuses:
            if status in health_counts:
                health_counts[status] += 1

    health_labels = list(health_counts.keys())
    health_counts_list = list(health_counts.values())

    # Get distinct counties for filter
    counties = [c[0] for c in db.session.query(Farmer.county).distinct().all() if c[0]]

    # ========== COUNTY COMPARISON ==========
    county_comparison = None
    if selected_county:
        # Health score for SELECTED county
        selected_score = db.session.query(
            func.avg(
                case(
                    (CropHealth.health_status == 'Healthy', 100),
                    (CropHealth.health_status == 'Fair', 50),
                    (CropHealth.health_status == 'Poor', 0),
                    else_=0
                )
            )
        ).join(Farmer, Farmer.id == CropHealth.farmer_id)\
         .filter(Farmer.county == selected_county)\
         .scalar() or 0

        # Health score for OTHER counties
        others_score = db.session.query(
            func.avg(
                case(
                    (CropHealth.health_status == 'Healthy', 100),
                    (CropHealth.health_status == 'Fair', 50),
                    (CropHealth.health_status == 'Poor', 0),
                    else_=0
                )
            )
        ).join(Farmer, Farmer.id == CropHealth.farmer_id)\
         .filter(Farmer.county != selected_county)\
         .scalar() or 0

        # Calculate difference
        difference = selected_score - others_score

        county_comparison = {
            'county_score': round(selected_score, 1),
            'others_score': round(others_score, 1),
            'difference': round(difference, 1),
            'trend': 'up' if difference > 0 else 'down' if difference < 0 else 'flat'
        }

    return render_template(
        'officer/officer_dashboard.html',
        # Filter options
        counties=counties,
        selected_county=selected_county,
        selected_period=selected_period,
        start_date=start_date,
        end_date=end_date,

        # Yield KPIs
        per_crop_yield=per_crop_yield,
        top_crop=top_crop,
        total_period_yield=round(total_period_yield, 1),
        comparison=comparison,

        # Your existing variables
        total_farmers=total_farmers,
        total_crops=total_crops,
        active_issues=active_issues,
        crop_names=crop_names,
        crop_yields=crop_yields,
        health_labels=health_labels,
        health_counts=health_counts_list,
        latest_health=latest_health,
        county_comparison=county_comparison
    )


@officer_bp.route('/farmer/<int:farmer_id>')
@login_required
def farmer_profile(farmer_id):
    
    if current_user.role != 'officer':
        return "Unauthorized", 403

    farmer = Farmer.query.get_or_404(farmer_id)

    farm_records = (
        FarmRecord.query
        .filter_by(farmer_id=farmer_id)
        .join(Crop)
        .all()
    )
    harvested_crop_ids = [record.crop_id for record in farm_records]
    
    # Using a subquery to get the latest date for each crop
    latest_per_crop = db.session.query(
        CropHealth.crop_id,
        func.max(CropHealth.date).label('latest_date')
    ).filter_by(farmer_id=farmer_id).group_by(CropHealth.crop_id).subquery()
    
    # Join back to get the full records
    crop_health = db.session.query(CropHealth).join(
        latest_per_crop,
        (CropHealth.crop_id == latest_per_crop.c.crop_id) &
        (CropHealth.date == latest_per_crop.c.latest_date)
    ).filter(CropHealth.farmer_id == farmer_id).all()

    # Add harvest status to each crop health record
    for record in crop_health:
        record.is_harvested = record.crop_id in harvested_crop_ids

    soil_health = (
        SoilHealth.query
        .filter_by(farmer_id=farmer_id)
        .order_by(SoilHealth.date.desc())
        .all()
    )
    
    # Build advisory_map for this farmer's crop health records
    crop_health_ids = [ch.id for ch in crop_health]
    advisories = Advisory.query.filter(Advisory.crop_health_id.in_(crop_health_ids)).all()
    
    advisory_map = {
        int(a.crop_health_id): a
        for a in advisories
        if a.crop_health_id is not None
    }
    # Also mark if advice is locked (crop is harvested)
    for ch_id in advisory_map:
        for record in crop_health:
            if record.id == ch_id and record.is_harvested:
                advisory_map[ch_id].is_locked = True
                break
                
    return render_template(
        'officer/farmer_profile.html',
        farmer=farmer,
        farm_records=farm_records,
        crop_health=crop_health,
        soil_health=soil_health,
        advisory_map=advisory_map
    )


@officer_bp.route('/advisory/<int:crop_health_id>', methods=['GET','POST'])
@login_required
def advisory(crop_health_id):
    
    if current_user.role != 'officer':
        return "Unauthorized", 403
      # Add debug print
    #print(f"Looking for crop_health_id: {crop_health_id}")
    
    crop_health = CropHealth.query.get_or_404(crop_health_id)
    # Check if crop has been harvested
    has_harvest = FarmRecord.query.filter_by(
        farmer_id=crop_health.farmer_id,
        crop_id=crop_health.crop_id
    ).first() is not None
    
    if has_harvest:
        flash(' Cannot give advice for harvested crops.', 'error')
        return redirect(url_for('officer.farmer_profile', farmer_id=crop_health.farmer_id))
    
    if request.method == 'POST':

        advisory = Advisory(
            farmer_id=crop_health.farmer_id,
            officer_id=current_user.id,
            crop_health_id=crop_health.id,
            recommendation=request.form['recommendation'],
            priority=request.form['priority']
        )

        db.session.add(advisory)
        db.session.commit()

        flash('Advisory saved successfully')

        return redirect(url_for('officer.officer_dashboard'))

    return render_template(
        'officer/add_advisory.html',
        crop_health=crop_health
                          )

@officer_bp.route('/advice/<int:advice_id>/edit', methods=['POST'])
@login_required
def edit_advice(advice_id):
    
    if current_user.role != 'officer':
        return "Unauthorized", 403
    
    advisory = Advisory.query.get_or_404(advice_id)
    crop_health_id = request.form.get('crop_health_id')
    
    # Check if crop has been harvested
    crop_health = CropHealth.query.get(crop_health_id)
    has_harvest = FarmRecord.query.filter_by(
        farmer_id=advisory.farmer_id,
        crop_id=crop_health.crop_id
    ).first() is not None
    
    if has_harvest:
        flash(' Cannot edit advice for harvested crops.', 'error')
        return redirect(url_for('officer.farmer_profile', farmer_id=advisory.farmer_id))
    
    # Check if the officer owns this advice
    if advisory.officer_id != current_user.id:
        flash('You can only edit your own advice.', 'error')
        return redirect(url_for('officer.farmer_profile', farmer_id=advisory.farmer_id))
    
    # Update the advice
    advisory.recommendation = request.form['recommendation']
    advisory.priority = request.form['priority']
    
    db.session.commit()
    flash(' Advice updated successfully.', 'success')
    
    # Redirect back to the farmer profile
    return redirect(url_for('officer.farmer_profile', farmer_id=advisory.farmer_id))

@officer_bp.route('/advice/<int:advice_id>/delete')
@login_required
def delete_advice(advice_id):
    
    if current_user.role != 'officer':
        return "Unauthorized", 403
    
    advisory = Advisory.query.get_or_404(advice_id)
    crop_health_id = request.args.get('crop_health_id')
    farmer_id = advisory.farmer_id
    
    # Check if crop has been harvested
    crop_health = CropHealth.query.get(crop_health_id)
    has_harvest = FarmRecord.query.filter_by(
        farmer_id=advisory.farmer_id,
        crop_id=crop_health.crop_id
    ).first() is not None
    
    if has_harvest:
        flash(' Cannot delete advice for harvested crops.', 'error')
        return redirect(url_for('officer.farmer_profile', farmer_id=advisory.farmer_id))
    
    # Check if the officer owns this advice
    if advisory.officer_id != current_user.id:
        flash('You can only delete your own advice.', 'error')
        return redirect(url_for('officer.farmer_profile', farmer_id=farmer_id))
    
    # Delete the advice
    db.session.delete(advisory)
    db.session.commit()
    flash(' Advice deleted successfully.', 'success')
    
    # Redirect back to the farmer profile
    return redirect(url_for('officer.farmer_profile', farmer_id=farmer_id))

# Optional: Add a route to view all advice for a farmer
@officer_bp.route('/farmer/<int:farmer_id>/advice')
@login_required
def view_farmer_advice(farmer_id):
    
    if current_user.role != 'officer':
        return "Unauthorized", 403
    
    
    farmer = Farmer.query.get_or_404(farmer_id)
    advisories = Advisory.query.filter_by(farmer_id=farmer_id)\
                               .order_by(Advisory.created_at.desc())\
                               .all()
    
    return render_template(
        'officer/farmer_advice.html',
        farmer=farmer,
        advisories=advisories
    )
