"""
Seed script for Courses and Syllabus data
Creates 6 courses with 14 weeks of syllabus each
All courses assigned to lecturer_id = 7
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Course, Syllabus, User
from app.models.user import UserRole

# Course data with codes, names, and descriptions
COURSES_DATA = [
    {
        "code": "DS101",
        "name": "Data Science",
        "description": "Comprehensive introduction to data science covering data collection, analysis, visualization, and machine learning fundamentals. Students will learn to work with real-world datasets using Python and modern data science tools."
    },
    {
        "code": "AI201",
        "name": "Artificial Intelligence",
        "description": "Explore the foundations of artificial intelligence including search algorithms, knowledge representation, machine learning, neural networks, and AI ethics. Covers both theoretical concepts and practical applications."
    },
    {
        "code": "SE301",
        "name": "Software Engineering",
        "description": "Learn software development methodologies, design patterns, testing strategies, version control, and DevOps practices. Focus on building maintainable, scalable software systems using industry best practices."
    },
    {
        "code": "IS401",
        "name": "Information Systems",
        "description": "Study of information systems in business contexts, covering enterprise systems, database management, information security, cloud computing, and digital transformation strategies."
    },
    {
        "code": "MM501",
        "name": "Multimedia",
        "description": "Introduction to multimedia systems covering digital text, graphics, audio, video, compression techniques, animation, 3D modeling, and interactive multimedia design."
    },
    {
        "code": "CSN601",
        "name": "Computer Systems & Networks",
        "description": "Comprehensive study of computer systems architecture, operating systems, networking fundamentals, protocols, network security, and distributed systems."
    }
]

# Syllabus data for each course (14 weeks)
SYLLABUS_DATA = {
    "DS101": [  # Data Science
        {"week": 1, "topic": "Introduction to Data Science & Tools (Python, Jupyter, Pandas)", "content": "Introduction to the field of data science, its applications, and career opportunities. Setting up Python environment, Jupyter Notebooks, and learning Pandas for data manipulation. Hands-on exercises with basic data operations."},
        {"week": 2, "topic": "Data Collection & Data Types", "content": "Methods of data collection including APIs, web scraping, and file imports. Understanding different data types (numerical, categorical, text, datetime). Data quality assessment and initial data exploration techniques."},
        {"week": 3, "topic": "Data Cleaning & Pre-processing", "content": "Identifying and handling missing values, outliers, and inconsistencies. Data transformation techniques including normalization, encoding categorical variables, and feature scaling. Best practices for data cleaning workflows."},
        {"week": 4, "topic": "Exploratory Data Analysis (EDA)", "content": "Statistical summaries, distribution analysis, and correlation studies. Using descriptive statistics to understand data patterns. Identifying relationships between variables and detecting anomalies."},
        {"week": 5, "topic": "Data Visualization (Matplotlib, Seaborn)", "content": "Creating effective visualizations using Matplotlib and Seaborn. Types of charts (bar, line, scatter, heatmaps, box plots). Design principles for clear and informative data visualizations."},
        {"week": 6, "topic": "Statistical Foundations (Distributions, Hypothesis Testing)", "content": "Probability distributions (normal, binomial, Poisson). Hypothesis testing concepts including p-values, confidence intervals, t-tests, and chi-square tests. Statistical significance and interpretation of results."},
        {"week": 7, "topic": "Probability & Sampling", "content": "Probability theory fundamentals, conditional probability, Bayes' theorem. Sampling methods (random, stratified, cluster sampling). Sample size determination and sampling bias."},
        {"week": 8, "topic": "Machine Learning Overview", "content": "Introduction to machine learning paradigms: supervised, unsupervised, and reinforcement learning. Model training, validation, and testing concepts. Overview of common ML algorithms and their use cases."},
        {"week": 9, "topic": "Supervised Learning (Regression)", "content": "Linear and polynomial regression models. Understanding overfitting and underfitting. Model evaluation metrics (R-squared, MSE, MAE). Practical implementation using scikit-learn."},
        {"week": 10, "topic": "Supervised Learning (Classification)", "content": "Classification algorithms including logistic regression, decision trees, and k-nearest neighbors. Evaluation metrics (accuracy, precision, recall, F1-score, ROC curves). Handling imbalanced datasets."},
        {"week": 11, "topic": "Unsupervised Learning (Clustering)", "content": "Clustering algorithms: K-means, hierarchical clustering, DBSCAN. Determining optimal number of clusters. Applications of clustering in data analysis and customer segmentation."},
        {"week": 12, "topic": "Feature Engineering & Model Evaluation", "content": "Feature selection and engineering techniques. Cross-validation methods. Hyperparameter tuning. Model comparison and selection strategies. Avoiding data leakage."},
        {"week": 13, "topic": "Big Data (Hadoop, Spark)", "content": "Introduction to big data concepts and challenges. Hadoop ecosystem overview. Apache Spark for distributed data processing. Working with large datasets and parallel computing."},
        {"week": 14, "topic": "Capstone: Mini Data Science Project", "content": "End-to-end data science project covering problem definition, data collection, cleaning, analysis, modeling, and presentation. Students apply all learned concepts to solve a real-world problem."}
    ],
    "AI201": [  # Artificial Intelligence
        {"week": 1, "topic": "Introduction to AI & History", "content": "Overview of artificial intelligence, its history, and evolution. Key milestones in AI development. Current state of AI and future prospects. Applications of AI across various industries."},
        {"week": 2, "topic": "Intelligent Agents & Environments", "content": "Concept of intelligent agents and their properties. Types of agents (simple reflex, model-based, goal-based, utility-based). Agent environments and their characteristics (observable, deterministic, episodic, etc.)."},
        {"week": 3, "topic": "Search Algorithms (Uninformed)", "content": "Uninformed search strategies: breadth-first search (BFS), depth-first search (DFS), uniform-cost search. Comparing search algorithms based on completeness, optimality, time and space complexity."},
        {"week": 4, "topic": "Search Algorithms (Informed – A*, heuristics)", "content": "Informed search algorithms: greedy best-first search, A* algorithm. Heuristic functions and admissibility. Designing effective heuristics for problem-solving."},
        {"week": 5, "topic": "Constraint Satisfaction Problems", "content": "Formulating problems as constraint satisfaction problems (CSPs). Backtracking search algorithms. Constraint propagation techniques. Applications in scheduling, planning, and configuration problems."},
        {"week": 6, "topic": "Game Playing (Minimax, Alpha-Beta)", "content": "Game theory basics. Minimax algorithm for optimal play in two-player games. Alpha-beta pruning for efficiency. Implementation in games like tic-tac-toe and chess."},
        {"week": 7, "topic": "Knowledge Representation", "content": "Methods of representing knowledge in AI systems. Semantic networks, frames, and scripts. Ontologies and knowledge graphs. Challenges in knowledge representation."},
        {"week": 8, "topic": "Propositional & First-Order Logic", "content": "Propositional logic syntax and semantics. First-order logic (predicate logic) and its expressiveness. Logical inference and resolution. Applications in automated reasoning."},
        {"week": 9, "topic": "Planning & Reasoning", "content": "Automated planning problems and solutions. STRIPS representation. Planning algorithms (forward and backward state-space search). Temporal and hierarchical planning."},
        {"week": 10, "topic": "Machine Learning Foundations", "content": "Introduction to machine learning in AI context. Learning from data: supervised, unsupervised, and reinforcement learning. Basic concepts of neural networks and their role in modern AI."},
        {"week": 11, "topic": "Neural Networks & Deep Learning", "content": "Artificial neural networks architecture. Deep learning fundamentals. Convolutional neural networks (CNNs) and recurrent neural networks (RNNs). Applications in image recognition and natural language processing."},
        {"week": 12, "topic": "Natural Language Processing", "content": "NLP fundamentals: tokenization, parsing, semantic analysis. Language models and word embeddings. Sentiment analysis and text classification. Recent advances in transformer models."},
        {"week": 13, "topic": "Reinforcement Learning", "content": "Reinforcement learning framework: agents, environments, rewards, policies. Q-learning and policy gradient methods. Applications in game playing, robotics, and autonomous systems."},
        {"week": 14, "topic": "AI Ethics & Future Trends", "content": "Ethical considerations in AI development and deployment. Bias, fairness, and transparency. AI safety and alignment. Future trends: AGI, AI governance, and societal impact."}
    ],
    "SE301": [  # Software Engineering
        {"week": 1, "topic": "Introduction to Software Engineering", "content": "Overview of software engineering discipline. Software development lifecycle (SDLC). Challenges in software development. Role of software engineers and career paths."},
        {"week": 2, "topic": "Software Process Models & Agile", "content": "Traditional process models: waterfall, V-model, spiral. Agile methodologies: Scrum, Kanban, Extreme Programming. Comparing different approaches and selecting appropriate models."},
        {"week": 3, "topic": "Requirements Engineering", "content": "Requirements gathering techniques: interviews, surveys, observation. Functional and non-functional requirements. Requirements documentation and specification. Requirements validation and management."},
        {"week": 4, "topic": "System Modeling (UML)", "content": "Unified Modeling Language (UML) basics. Use case diagrams, class diagrams, sequence diagrams. Modeling software systems for better understanding and communication."},
        {"week": 5, "topic": "Software Architecture", "content": "Software architecture patterns: layered, MVC, microservices, event-driven. Architectural design decisions. Scalability and maintainability considerations. Documenting software architecture."},
        {"week": 6, "topic": "Design Patterns", "content": "Common design patterns: creational, structural, and behavioral patterns. Singleton, Factory, Observer, Strategy patterns. When and how to apply design patterns effectively."},
        {"week": 7, "topic": "Testing Fundamentals", "content": "Software testing principles and importance. Types of testing: functional, non-functional, white-box, black-box. Test planning and test case design. Testing strategies and approaches."},
        {"week": 8, "topic": "Unit & Integration Testing", "content": "Unit testing principles and best practices. Test-driven development (TDD). Integration testing strategies. Mocking and test doubles. Writing maintainable test code."},
        {"week": 9, "topic": "Software Quality Assurance", "content": "Quality assurance processes and standards. Code reviews and inspections. Static analysis tools. Quality metrics and measurement. Continuous quality improvement."},
        {"week": 10, "topic": "Version Control & CI/CD", "content": "Version control systems (Git). Branching strategies and workflows. Continuous Integration (CI) and Continuous Deployment (CD). Automated build and deployment pipelines."},
        {"week": 11, "topic": "DevOps Concepts", "content": "DevOps culture and practices. Infrastructure as Code (IaC). Containerization with Docker. Container orchestration basics. Monitoring and logging in production."},
        {"week": 12, "topic": "Software Maintenance & Documentation", "content": "Types of software maintenance: corrective, adaptive, perfective, preventive. Documentation standards and best practices. Code documentation and API documentation. Knowledge management."},
        {"week": 13, "topic": "Project Management", "content": "Software project management fundamentals. Estimation techniques. Risk management. Team collaboration and communication. Project tracking and reporting."},
        {"week": 14, "topic": "Group Project / Case Study", "content": "Hands-on group project applying all software engineering concepts. Real-world case study analysis. Project presentation and lessons learned. Industry best practices review."}
    ],
    "IS401": [  # Information Systems
        {"week": 1, "topic": "Introduction to IS & Digital Transformation", "content": "Overview of information systems and their role in organizations. Digital transformation concepts and drivers. Types of information systems. Impact of IS on business operations."},
        {"week": 2, "topic": "Business Processes & Enterprise Systems", "content": "Understanding business processes and workflow. Enterprise Resource Planning (ERP) systems. Customer Relationship Management (CRM). Supply Chain Management (SCM) systems."},
        {"week": 3, "topic": "Systems Thinking", "content": "Systems thinking approach to problem-solving. System components and interactions. Feedback loops and system dynamics. Applying systems thinking to IS design and implementation."},
        {"week": 4, "topic": "Requirements Gathering & Analysis", "content": "IS requirements gathering techniques. Business analysis methods. Process modeling and documentation. Stakeholder analysis and engagement. Requirements prioritization."},
        {"week": 5, "topic": "Database Concepts in IS", "content": "Database fundamentals for information systems. Relational database design. SQL basics for IS professionals. Data modeling and entity-relationship diagrams. Database management in IS context."},
        {"week": 6, "topic": "Information Security Basics", "content": "Information security fundamentals. Threats and vulnerabilities. Security controls and countermeasures. Access control and authentication. Security policies and compliance."},
        {"week": 7, "topic": "Networked Information Systems", "content": "Network architectures for information systems. Local Area Networks (LANs) and Wide Area Networks (WANs). Network protocols and standards. Network security considerations."},
        {"week": 8, "topic": "Cloud Computing", "content": "Cloud computing models: IaaS, PaaS, SaaS. Cloud deployment models: public, private, hybrid. Cloud service providers and selection criteria. Cloud migration strategies."},
        {"week": 9, "topic": "IS Infrastructure Management", "content": "IT infrastructure components and management. Server management and virtualization. Storage systems and backup strategies. Disaster recovery and business continuity planning."},
        {"week": 10, "topic": "IS Strategy & Governance", "content": "Information systems strategy alignment with business goals. IT governance frameworks. IS investment decisions and ROI. Managing IS resources and capabilities."},
        {"week": 11, "topic": "Business Analytics & Decision Support", "content": "Business intelligence and analytics. Data warehousing concepts. Decision support systems (DSS). Executive information systems (EIS). Using data for strategic decision-making."},
        {"week": 12, "topic": "E-Business & E-Commerce", "content": "E-business models and strategies. E-commerce platforms and technologies. Online payment systems. Digital marketing and customer engagement. Legal and ethical considerations."},
        {"week": 13, "topic": "Emerging Technologies in IS", "content": "Current and emerging technologies: IoT, blockchain, AI/ML in business. Impact on information systems. Technology adoption strategies. Future trends in IS."},
        {"week": 14, "topic": "Case Study: IS Implementation Project", "content": "Comprehensive case study of real-world IS implementation. Analysis of challenges, solutions, and outcomes. Lessons learned and best practices. Group presentation and discussion."}
    ],
    "MM501": [  # Multimedia
        {"week": 1, "topic": "Introduction to Multimedia Systems", "content": "Overview of multimedia systems and applications. Components of multimedia: text, graphics, audio, video. Multimedia hardware and software requirements. Career opportunities in multimedia."},
        {"week": 2, "topic": "Digital Text & Graphics", "content": "Text representation and encoding. Font technologies and typography. Vector and raster graphics. Image formats (PNG, JPEG, SVG). Graphics editing tools and techniques."},
        {"week": 3, "topic": "Digital Audio", "content": "Audio fundamentals: sampling, quantization, encoding. Audio file formats (MP3, WAV, AAC). Audio editing and processing. Sound design principles. Audio compression techniques."},
        {"week": 4, "topic": "Digital Video", "content": "Video fundamentals: frame rate, resolution, color depth. Video file formats (MP4, AVI, MOV). Video capture and editing basics. Video compression and codecs."},
        {"week": 5, "topic": "Image Compression", "content": "Image compression principles and techniques. Lossless vs. lossy compression. JPEG compression algorithm. PNG and GIF formats. Choosing appropriate compression methods."},
        {"week": 6, "topic": "Video Compression", "content": "Video compression algorithms and standards. H.264, H.265 codecs. Motion compensation and prediction. Bitrate control and quality settings. Streaming video considerations."},
        {"week": 7, "topic": "Multimedia Networking", "content": "Network requirements for multimedia delivery. Streaming protocols (RTSP, HLS, DASH). Quality of Service (QoS) for multimedia. Bandwidth considerations. Real-time multimedia communication."},
        {"week": 8, "topic": "Multimedia File Formats & Standards", "content": "Standard multimedia formats and containers. MP4, AVI, MKV containers. Codec selection and compatibility. Metadata in multimedia files. Industry standards and specifications."},
        {"week": 9, "topic": "Animation Techniques", "content": "Animation principles and techniques. Keyframe animation. Tweening and interpolation. 2D animation tools and workflows. Timeline-based animation."},
        {"week": 10, "topic": "3D Modeling Basics", "content": "3D modeling fundamentals. Polygonal modeling techniques. Texturing and materials. Lighting and rendering basics. Introduction to 3D software tools."},
        {"week": 11, "topic": "Game Multimedia", "content": "Multimedia in game development. Game assets: sprites, textures, audio, animations. Game engines and multimedia integration. Performance optimization for games."},
        {"week": 12, "topic": "Interactive Multimedia Design", "content": "Design principles for interactive multimedia. User interface design for multimedia applications. Interactivity and user engagement. Multimedia authoring concepts."},
        {"week": 13, "topic": "Multimedia Authoring Tools", "content": "Overview of multimedia authoring software. Adobe Creative Suite, Blender, Unity. Workflow and best practices. Creating multimedia presentations and applications."},
        {"week": 14, "topic": "Final Multimedia Project", "content": "Comprehensive multimedia project integrating all learned concepts. Project planning and execution. Presentation of final work. Portfolio development and career preparation."}
    ],
    "CSN601": [  # Computer Systems & Networks
        {"week": 1, "topic": "Introduction to Computer Systems", "content": "Overview of computer system components and architecture. CPU, memory, storage, and I/O devices. System performance metrics. Evolution of computer systems."},
        {"week": 2, "topic": "CPU Architecture", "content": "CPU components and organization. Instruction set architecture (ISA). Pipelining and parallel processing. CPU performance optimization. Modern processor architectures."},
        {"week": 3, "topic": "Memory Hierarchy", "content": "Memory hierarchy: registers, cache, RAM, storage. Cache organization and replacement policies. Virtual memory concepts. Memory management techniques."},
        {"week": 4, "topic": "Operating Systems Basics", "content": "Operating system functions and services. Process and memory management. File systems. OS types: Windows, Linux, macOS. OS installation and configuration."},
        {"week": 5, "topic": "Processes & Threads", "content": "Process concept and lifecycle. Process scheduling algorithms. Multithreading and concurrency. Thread synchronization and communication. Deadlock prevention and detection."},
        {"week": 6, "topic": "Networking Fundamentals", "content": "Network basics: nodes, links, topologies. Network types: LAN, WAN, MAN. Network hardware: routers, switches, hubs. Basic networking concepts and terminology."},
        {"week": 7, "topic": "OSI Model", "content": "OSI (Open Systems Interconnection) model layers. TCP/IP model comparison. Protocol stack and encapsulation. Understanding each layer's functions and protocols."},
        {"week": 8, "topic": "IP Addressing & Routing", "content": "IPv4 and IPv6 addressing. Subnetting and CIDR notation. Routing algorithms and protocols (RIP, OSPF, BGP). Network address translation (NAT)."},
        {"week": 9, "topic": "Transport Layer (TCP/UDP)", "content": "Transport layer protocols: TCP and UDP. TCP connection management and flow control. UDP characteristics and use cases. Port numbers and socket programming basics."},
        {"week": 10, "topic": "Network Security Basics", "content": "Network security threats and vulnerabilities. Firewalls and intrusion detection systems. VPNs and secure communication. Network security best practices."},
        {"week": 11, "topic": "Wireless & Mobile Networks", "content": "Wireless networking technologies: WiFi, Bluetooth, cellular. Mobile network generations (4G, 5G). Wireless security considerations. Mobile device management."},
        {"week": 12, "topic": "Cloud Infrastructure", "content": "Cloud computing infrastructure. Virtualization and containerization. Cloud networking and storage. Infrastructure as a Service (IaaS) concepts."},
        {"week": 13, "topic": "Distributed Systems", "content": "Distributed system architectures. Distributed computing challenges. Consistency and replication. Distributed algorithms and protocols. Cloud and edge computing."},
        {"week": 14, "topic": "Network Simulation / Lab Project", "content": "Hands-on network simulation and configuration. Using network simulation tools (Packet Tracer, GNS3). Network troubleshooting and analysis. Final project presentation."}
    ]
}

def seed_courses_and_syllabus(db: Session, lecturer_id: int = 7):
    """
    Seed courses and syllabus data
    All courses are assigned to the specified lecturer_id
    """
    print(f"🌱 Starting seed process for lecturer_id = {lecturer_id}")
    
    # Verify lecturer exists
    lecturer = db.query(User).filter(
        User.id == lecturer_id,
        User.role == UserRole.LECTURER
    ).first()
    
    if not lecturer:
        print(f"❌ Error: Lecturer with ID {lecturer_id} not found or is not a lecturer")
        return
    
    print(f"✅ Found lecturer: {lecturer.full_name} ({lecturer.email})")
    
    # Create courses
    created_courses = {}
    for course_data in COURSES_DATA:
        # Check if course already exists
        existing_course = db.query(Course).filter(Course.code == course_data["code"]).first()
        if existing_course:
            print(f"⚠️  Course {course_data['code']} already exists, skipping...")
            created_courses[course_data["code"]] = existing_course
            continue
        
        from datetime import datetime
        course = Course(
            code=course_data["code"],
            name=course_data["name"],
            description=course_data["description"],
            lecturer_id=lecturer_id,
            updated_at=datetime.now()
        )
        db.add(course)
        db.flush()  # Get the ID without committing
        created_courses[course_data["code"]] = course
        print(f"✅ Created course: {course_data['code']} - {course_data['name']}")
    
    db.commit()
    print(f"\n✅ Created {len(created_courses)} courses\n")
    
    # Create syllabus for each course
    total_syllabus_created = 0
    for course_code, course in created_courses.items():
        if course_code not in SYLLABUS_DATA:
            print(f"⚠️  No syllabus data found for {course_code}")
            continue
        
        print(f"📚 Creating syllabus for {course_code}...")
        syllabus_entries = SYLLABUS_DATA[course_code]
        
        for entry_data in syllabus_entries:
            # Check if syllabus entry already exists
            existing = db.query(Syllabus).filter(
                Syllabus.course_id == course.id,
                Syllabus.week_number == entry_data["week"],
                Syllabus.is_active == True
            ).first()
            
            if existing:
                print(f"  ⚠️  Week {entry_data['week']} already exists, skipping...")
                continue
            
            syllabus = Syllabus(
                course_id=course.id,
                week_number=entry_data["week"],
                topic=entry_data["topic"],
                content=entry_data["content"],
                version=1,
                is_active=True,
                created_by=lecturer_id,
                change_reason="Initial seed data"
            )
            db.add(syllabus)
            total_syllabus_created += 1
        
        db.commit()
        print(f"  ✅ Created {len(syllabus_entries)} weeks for {course_code}\n")
    
    print(f"🎉 Seed complete!")
    print(f"   - Courses: {len(created_courses)}")
    print(f"   - Syllabus entries: {total_syllabus_created}")
    print(f"   - All assigned to lecturer: {lecturer.full_name} (ID: {lecturer_id})")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_courses_and_syllabus(db, lecturer_id=7)
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

