# FarmXpert Onboarding System

A comprehensive 15-step interactive onboarding flow for new FarmXpert users.

## Features

- **15 Beautiful Steps**: Welcome, Location, Farm Details, Equipment, and more
- **Smooth Animations**: Framer Motion powered transitions between steps
- **Visual Selection**: Lucide React icons for all selectable options
- **Progress Tracking**: Visual progress bar showing completion status
- **Smart Validation**: Step-by-step validation with clear error messages
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Database Integration**: Saves all onboarding data to the database

## Onboarding Steps

1. **Welcome & Farm Name** - User enters their farm name
2. **Location** - State and district selection
3. **Farm Size** - Farm size in acres
4. **Soil Type** - Primary soil type (Clay, Sandy, Loamy, etc.)
5. **Crop Category** - Main crop category (Cereals, Pulses, etc.)
6. **Specific Crop** - Specific crop or variety
7. **Irrigation Method** - Drip, Sprinkler, Rainfed, etc.
8. **Water Quality** - Fresh, Saline, Brackish
9. **IoT Setup** - Current hardware/IoT setup
10. **Farming Goals** - Primary farming objectives
11. **Fertilizer Preference** - Chemical, Organic, or Integrated
12. **Pest Management** - Preventive, Reactive, or Biological
13. **Machinery** - Available equipment (multi-select)
14. **Labor Setup** - Family, Hired, or Mechanized
15. **Review & Submit** - Summary and final submission

## Setup Instructions

### 1. Database Migration

Run the SQL migration to add the `onboarding_completed` column:

```sql
-- Run this script on your database
-- File: scripts/add_onboarding_column.sql
```

### 2. Backend Integration

The onboarding system is already integrated with:

- **Auth Routes**: `/api/auth/onboarding/complete` endpoint
- **User Model**: Added `onboarding_completed` field
- **Auth Service**: `complete_user_onboarding()` method
- **Response Schemas**: Updated to include onboarding status

### 3. Frontend Integration

The onboarding flow is automatically triggered when:

- A new user registers for the first time
- An existing user logs in without completing onboarding
- User navigates to `/onboarding` route

### 4. Flow Logic

```
User Registers → Login → Check onboarding_completed
                                ↓
                        If False → Redirect to /onboarding
                                ↓
                        Complete 15 steps → Submit data
                                ↓
                        Mark onboarding_completed = True
                                ↓
                        Redirect to /dashboard
```

## File Structure

```
backend/
├── farmxpert/

frontend/src/
│   ├── auth/
│   │   ├── FarmOnboarding.jsx          # Main onboarding component
│   │   └── FarmOnboarding.module.css   # Styling
│   ├── components/auth/
│   │   └── OnboardingRoute.jsx         # Route protection logic
│   ├── contexts/AuthContext.jsx        # Updated with onboarding state
│   └── App.js                          # Route configuration
backend/farmxpert/interfaces/api/routes/
│   └── auth_routes.py                  # Onboarding API endpoint
backend/farmxpert/services/
│   └── auth_service.py                 # Onboarding business logic
backend/farmxpert/models/
│   └── user_models.py                  # Updated User model
backend/farmxpert/scripts/
    ├── add_onboarding_column.sql       # Database migration
    └── test_onboarding.py              # Integration tests
```

## API Endpoints

### Complete Onboarding
```
POST /api/auth/onboarding/complete
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "farmName": "My Farm",
  "state": "Maharashtra",
  "district": "Pune",
  "farmSize": "10",
  "soilType": "loamy",
  "mainCropCategory": "cereals",
  "specificCrop": "Wheat",
  "irrigationMethod": "drip",
  "waterSourceQuality": "fresh",
  "iotSetup": "basic",
  "primaryGoal": "yield",
  "fertilizerPreference": "integrated",
  "pestManagement": "preventive",
  "machinery": ["tractor"],
  "laborSetup": "family"
}
```

**Response:**
```json
{
  "message": "Onboarding completed successfully",
  "success": true
}
```

## Testing

Run the integration test:

```bash
cd backend/farmxpert
python scripts/test_onboarding.py
```

## Customization

### Adding New Steps

1. Update `FarmOnboarding.jsx`:
   - Add new step number to `canProceed()` function
   - Add new case in `renderStep()` function
   - Update progress bar calculation (15 steps total)

2. Update backend schemas:
   - Add new fields to `OnboardingData` model
   - Update database schema if needed

### Modifying Questions

Edit the step content in `FarmOnboarding.jsx`:
- Update question text
- Modify options arrays
- Change icons as needed

### Styling Changes

Modify `FarmOnboarding.module.css`:
- Update colors, spacing, animations
- Add responsive breakpoints
- Customize card/chip styles

## Troubleshooting

### Onboarding Not Triggering

1. Check if `onboarding_completed` column exists in database
2. Verify user object has `onboarding_completed` field
3. Check `needsOnboarding` state in AuthContext

### API Errors

1. Ensure backend server is running
2. Check authentication headers
3. Verify database connection

### Styling Issues

1. Check CSS module imports
2. Verify responsive breakpoints
3. Test on different screen sizes

## Future Enhancements

- [ ] Save onboarding data to dedicated farm profile table
- [ ] Add progress saving (resume later)
- [ ] Include conditional logic based on previous answers
- [ ] Add analytics tracking for onboarding completion
- [ ] Implement A/B testing for different question flows
- [ ] Add multi-language support

## Support

For issues or questions about the onboarding system:
1. Check this documentation
2. Run the test script to identify issues
3. Review browser console for frontend errors
4. Check backend logs for API errors
