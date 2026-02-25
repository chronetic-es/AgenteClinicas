DROP TABLE IF EXISTS RoomAssignments CASCADE;
DROP TABLE IF EXISTS Bookings CASCADE;
DROP TABLE IF EXISTS Rooms CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS RoomTypes CASCADE;

DROP TYPE IF EXISTS room_status;
DROP TYPE IF EXISTS booking_status;


CREATE TYPE room_status AS ENUM ('Available', 'Dirty', 'Maintenance');
CREATE TYPE booking_status AS ENUM ('Pending', 'Confirmed', 'CheckedIn', 'Completed', 'Cancelled');


CREATE TABLE RoomTypes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    max_occupancy INT NOT NULL,
    extra_bed_available BOOLEAN NOT NULL DEFAULT FALSE,
    extra_bed_price DECIMAL(10, 2) NULL,
    description TEXT
);

CREATE TABLE Rooms (
    id SERIAL PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    room_type_id INT REFERENCES RoomTypes(id),
    status room_status DEFAULT 'Available'
);

CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Bookings (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(id) NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    total_amount DECIMAL(10, 2),
    status booking_status DEFAULT 'Pending',
    desayuno_incluido BOOLEAN NOT NULL DEFAULT FALSE,
    transporte_aeropuerto BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT valid_dates CHECK (check_out_date > check_in_date)
);


CREATE TABLE RoomAssignments (
    id SERIAL PRIMARY KEY,
    booking_id INT REFERENCES Bookings(id) ON DELETE CASCADE,
    room_id INT REFERENCES Rooms(id),
    extra_bed BOOLEAN NOT NULL DEFAULT FALSE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO RoomTypes (name, base_price, max_occupancy, extra_bed_available, extra_bed_price, description) VALUES
('Habitación Individual', 80.00, 1, FALSE, NULL, 'Acogedora habitación individual con cama simple, escritorio y baño privado. Ideal para viajeros solos.'),
('Habitación Doble Estándar', 120.00, 2, TRUE, 20.00, 'Habitación doble con cama de matrimonio, amplio baño y todas las comodidades esenciales.'),
('Habitación Superior', 160.00, 2, TRUE, 30.00, 'Habitación doble superior con vistas, decoración premium, minibar y zona de trabajo.'),
('Junior Suite', 220.00, 2, TRUE, 40.00, 'Suite junior con sala de estar separada, bañera de hidromasaje y servicio de mayordomía.'),
('Suite Presidencial', 350.00, 2, TRUE, 60.00, 'Nuestra suite más exclusiva: salón privado, terraza, jacuzzi y atención personalizada 24h.');

INSERT INTO Rooms (room_number, room_type_id, status) VALUES
('101', 1, 'Available'),
('102', 1, 'Available'),
('201', 2, 'Available'),
('202', 2, 'Available'),
('301', 3, 'Available'),
('302', 3, 'Available'),
('401', 4, 'Available'),
('501', 5, 'Available');

INSERT INTO Users (full_name, phone) VALUES
('John Doe', '555-0199'),
('Jane Smith', '555-0122');

INSERT INTO Bookings (user_id, check_in_date, check_out_date, total_amount, status) VALUES
(1, '2026-06-10', '2026-06-13', 360.00, 'Confirmed');

INSERT INTO RoomAssignments (booking_id, room_id, extra_bed) VALUES (1, 3, FALSE);
