from enum import Enum


class TripStatus(str, Enum):
    PLANNING = "planning"
    VOTING = "voting"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"


class MemberRole(str, Enum):
    ORGANIZER = "organizer"
    MEMBER = "member"


class MemberStatus(str, Enum):
    INVITED = "invited"
    JOINED = "joined"
    DECLINED = "declined"
    LEFT = "left"
    

class TravelerType(str, Enum):
    SOLO = "solo"
    COUPLE = "couple"
    FAMILY = "family"
    FRIENDS = "friends"


class BudgetRange(str, Enum):
    RANGE_5_10K = "5k_10k"
    RANGE_10_20K = "10k_20k"
    RANGE_20_40K = "20k_40k"
    RANGE_40K_PLUS = "40k_plus"


class ClimatePreference(str, Enum):
    COLD = "cold"
    MODERATE = "moderate"
    WARM = "warm"
    NO_PREFERENCE = "no_preference"


class AccommodationPref(str, Enum):
    BUDGET = "budget"
    MID = "mid"
    LUXURY = "luxury"


class TransportPref(str, Enum):
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAR = "car"


class FoodPref(str, Enum):
    VEG = "veg"
    NON_VEG = "non_veg"
    VEGAN = "vegan"
    NO_PREFERENCE = "no_preference"


class TravelPriority(str, Enum):
    CHEAPEST = "cheapest"
    BALANCED = "balanced"
    COMFORT = "comfort"
    EXPERIENCE = "experience"


class TravelStyle(str, Enum):
    ADVENTURE = "adventure"
    NATURE = "nature"
    RELAXATION = "relaxation"
    CULTURAL = "cultural"
    NIGHTLIFE = "nightlife"
    FOOD = "food"


class Activity(str, Enum):
    TREKKING = "trekking"
    BEACH = "beach"
    HISTORICAL_PLACES = "historical_places"
    SHOPPING = "shopping"
    LOCAL_FOOD = "local_food"
    CAMPING = "camping"
    SIGHTSEEING = "sightseeing"
    WATER_SPORTS = "water_sports"
    WILDLIFE = "wildlife"
    PHOTOGRAPHY = "photography"
    NIGHTLIFE = "nightlife"
    SPA_WELLNESS = "spa_wellness"