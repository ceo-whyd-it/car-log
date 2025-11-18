"""
Core matching algorithms for trip reconstruction.

Implements:
- GPS matching with Haversine distance (70% weight)
- Address matching with normalization (30% weight)
- Hybrid scoring with bonuses
"""

import math
import re
import unicodedata
from typing import Dict, Tuple, Optional


# GPS Scoring Thresholds
GPS_SCORE_THRESHOLDS = [
    (100, 100),      # < 100m → 100 points
    (500, 90),       # 100m-500m → 90 points
    (2000, 70),      # 500m-2000m → 70 points
    (5000, 40),      # 2000m-5000m → 40 points
]

# Weights for hybrid scoring
GPS_WEIGHT = 0.7      # 70% GPS
ADDRESS_WEIGHT = 0.3  # 30% Address


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate Haversine distance between two GPS coordinates.

    Args:
        lat1, lon1: First coordinate (degrees)
        lat2, lon2: Second coordinate (degrees)

    Returns:
        Distance in meters
    """
    # Earth radius in meters
    R = 6371000

    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def score_gps_match(distance_meters: float) -> int:
    """
    Score GPS match based on distance.

    Args:
        distance_meters: Distance in meters

    Returns:
        Score from 0-100
    """
    for threshold, score in GPS_SCORE_THRESHOLDS:
        if distance_meters < threshold:
            return score

    # > 5000m
    return 0


def normalize_text(text: str) -> str:
    """
    Normalize text for matching: lowercase, remove accents.

    Slovak characters:
    - á → a, č → c, ď → d, é → e, í → i
    - ĺ → l, ľ → l, ň → n, ó → o, ô → o
    - ŕ → r, š → s, ť → t, ú → u, ý → y, ž → z

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove diacritics using NFD normalization
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text


def extract_address_components(address: str) -> Dict[str, str]:
    """
    Extract address components (city, street, POI).

    Args:
        address: Full address string

    Returns:
        Dictionary with components
    """
    if not address:
        return {}

    normalized = normalize_text(address)
    components = {}

    # Extract city (common Slovak cities)
    cities = [
        'bratislava', 'kosice', 'presov', 'zilina', 'banska bystrica',
        'nitra', 'trnava', 'martin', 'trencin', 'poprad'
    ]

    for city in cities:
        if city in normalized:
            components['city'] = city
            break

    # Extract street number pattern
    street_match = re.search(r'([a-z\s]+)\s+(\d+)', normalized)
    if street_match:
        components['street'] = street_match.group(1).strip()
        components['number'] = street_match.group(2)

    # Store full normalized address
    components['full'] = normalized

    return components


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    Args:
        s1, s2: Strings to compare

    Returns:
        Edit distance
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def score_address_match(address1: Optional[str], address2: Optional[str]) -> int:
    """
    Score address match using component-based similarity.

    Args:
        address1: First address
        address2: Second address

    Returns:
        Score from 0-100
    """
    if not address1 or not address2:
        return 0

    components1 = extract_address_components(address1)
    components2 = extract_address_components(address2)

    if not components1 or not components2:
        return 0

    score = 0

    # City match (40 points)
    if components1.get('city') == components2.get('city'):
        score += 40

    # Street match (30 points)
    if 'street' in components1 and 'street' in components2:
        street1 = components1['street']
        street2 = components2['street']
        max_len = max(len(street1), len(street2))

        if max_len > 0:
            distance = levenshtein_distance(street1, street2)
            similarity = 1 - (distance / max_len)
            score += int(similarity * 30)

    # Full address similarity (30 points)
    full1 = components1.get('full', '')
    full2 = components2.get('full', '')
    max_len = max(len(full1), len(full2))

    if max_len > 0:
        distance = levenshtein_distance(full1, full2)
        similarity = 1 - (distance / max_len)
        score += int(similarity * 30)

    return min(score, 100)


def calculate_hybrid_score(
    gap_coords: Tuple[float, float],
    template_coords: Tuple[float, float],
    gap_address: Optional[str] = None,
    template_address: Optional[str] = None,
    template_distance_km: Optional[float] = None,
    gap_distance_km: Optional[float] = None,
    gap_day_of_week: Optional[str] = None,
    template_typical_days: Optional[list] = None,
) -> Dict[str, any]:
    """
    Calculate hybrid matching score (GPS 70% + Address 30%).

    Args:
        gap_coords: (lat, lng) of gap checkpoint
        template_coords: (lat, lng) of template endpoint
        gap_address: Optional address of gap checkpoint
        template_address: Optional address of template endpoint
        template_distance_km: Optional template distance
        gap_distance_km: Optional gap distance
        gap_day_of_week: Optional day of week (e.g., "Monday")
        template_typical_days: Optional list of typical days

    Returns:
        Dictionary with scores and breakdown
    """
    # GPS matching (mandatory)
    distance_meters = haversine_distance(
        gap_coords[0], gap_coords[1],
        template_coords[0], template_coords[1]
    )
    gps_score = score_gps_match(distance_meters)

    # Address matching (optional)
    address_score = 0
    if gap_address and template_address:
        address_score = score_address_match(gap_address, template_address)

    # Base hybrid score
    base_score = (gps_score * GPS_WEIGHT) + (address_score * ADDRESS_WEIGHT)

    # Distance bonus (up to +10 points)
    distance_bonus = 0
    if template_distance_km and gap_distance_km:
        distance_diff = abs(template_distance_km - gap_distance_km)
        distance_diff_pct = distance_diff / template_distance_km if template_distance_km > 0 else 0

        if distance_diff_pct < 0.1:  # Within 10%
            distance_bonus = 10
        elif distance_diff_pct < 0.2:  # Within 20%
            distance_bonus = 5

    # Day-of-week bonus (up to +10 points)
    day_bonus = 0
    if gap_day_of_week and template_typical_days:
        if gap_day_of_week in template_typical_days:
            day_bonus = 10

    # Total score (capped at 100)
    total_score = min(base_score + distance_bonus + day_bonus, 100)

    return {
        'total_score': round(total_score, 2),
        'gps_score': gps_score,
        'address_score': address_score,
        'distance_meters': round(distance_meters, 2),
        'distance_bonus': distance_bonus,
        'day_bonus': day_bonus,
        'breakdown': {
            'gps_contribution': round(gps_score * GPS_WEIGHT, 2),
            'address_contribution': round(address_score * ADDRESS_WEIGHT, 2),
            'bonuses': distance_bonus + day_bonus,
        }
    }


def match_checkpoint_to_template(
    gap_checkpoint: Dict,
    template: Dict,
    endpoint: str = 'from',  # 'from' or 'to'
    gap_distance_km: Optional[float] = None,
    gap_day_of_week: Optional[str] = None,
) -> Dict:
    """
    Match a gap checkpoint to a template endpoint.

    Args:
        gap_checkpoint: Checkpoint data with location
        template: Template data
        endpoint: 'from' or 'to' endpoint to match
        gap_distance_km: Optional gap distance for distance bonus
        gap_day_of_week: Optional day of week for day bonus

    Returns:
        Match result with score and details
    """
    # Extract gap checkpoint data
    gap_location = gap_checkpoint.get('location', {})
    gap_coords_data = gap_location.get('coords')

    if not gap_coords_data:
        return {
            'success': False,
            'error': 'Gap checkpoint missing GPS coordinates'
        }

    gap_coords = (gap_coords_data['latitude'], gap_coords_data['longitude'])
    gap_address = gap_location.get('address')

    # Extract template endpoint data
    if endpoint == 'from':
        template_coords_data = template.get('from_coords')
        template_address = template.get('from_address')
    else:
        template_coords_data = template.get('to_coords')
        template_address = template.get('to_address')

    if not template_coords_data:
        return {
            'success': False,
            'error': f'Template missing {endpoint}_coords'
        }

    template_coords = (template_coords_data['lat'], template_coords_data['lng'])

    # Calculate hybrid score
    score_result = calculate_hybrid_score(
        gap_coords=gap_coords,
        template_coords=template_coords,
        gap_address=gap_address,
        template_address=template_address,
        template_distance_km=template.get('distance_km'),
        gap_distance_km=gap_distance_km,
        gap_day_of_week=gap_day_of_week,
        template_typical_days=template.get('typical_days'),
    )

    return {
        'success': True,
        'endpoint': endpoint,
        'score': score_result['total_score'],
        'details': score_result,
    }
