from flask import Blueprint, jsonify, request
from app.models.location import Location

locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/provinces')
def get_provinces():
    provinces = Location.query.filter_by(level='province').all()
    return jsonify([province.to_dict() for province in provinces])

@locations_bp.route('/districts/<province_code>')
def get_districts(province_code):
    districts = Location.query.filter_by(level='district', parent_code=province_code).all()
    return jsonify([district.to_dict() for district in districts])

@locations_bp.route('/wards/<district_code>')
def get_wards(district_code):
    wards = Location.query.filter_by(level='ward', parent_code=district_code).all()
    return jsonify([ward.to_dict() for ward in wards])

@locations_bp.route('/hamlets/<ward_code>')
def get_hamlets(ward_code):
    hamlets = Location.query.filter_by(level='hamlet', parent_code=ward_code).all()
    return jsonify([hamlet.to_dict() for hamlet in hamlets]) 