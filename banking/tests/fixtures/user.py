from server.models.enums import UserRole

SAMPLE_USER_CONTACT_DETAILS = {
    "email": "fake@user.net",
    "phone": "+234907282824",
    "address": "St George Town, Middle of Nowhere",
    "city": "Ghost Town",
    "state": "Georgia",
    "zip_code": "373882",
    "country": "Nigeria",
    
}

SAMPLE_USER_DATA = {
    "first_name": "John",
    "last_name":"Doe",
    "username": "Iron Man",
    "date_of_birth": "2000-07-09",
    "role": UserRole.CUSTOMER,
    "password": "Password"
    
}