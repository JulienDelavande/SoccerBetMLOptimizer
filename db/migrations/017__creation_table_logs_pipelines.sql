CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    service VARCHAR(50),
    module VARCHAR(50),
    name VARCHAR(255),
    level VARCHAR(50),
    message TEXT,
    filename VARCHAR(255),
    lineno INT
);
